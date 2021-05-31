import * as d3 from 'd3'
import { type } from 'jquery';
<script src="https://d3js.org/d3.v6.js"></script>

var NODE_RADIUS = 20;
var NODE_BUFFER = 40;
var MOVE_STRENGTH = .4;
var STROKE_WIDTH = 2;

export const generateChart2 = (courses, loc, toggleCourse) => {
	var width  = loc.parent().width();
	var height = loc.parent().height();
	var margin = {
		top: 50,
		bottom: 50,
		left: 50,
		right: 50,
	};
    var link_color = "#555";
	
    d3.select("svg").remove();

	var svg = d3.select(loc[0])
	            .append("svg")
				.attr("width", width)
				.attr("height", height)
				.append('g')
				.attr('transform', 'translate(' + margin.top + ',' + margin.left + ')');
	
	width = width - margin.left - margin.right;
	height = height - margin.top - margin.bottom;
	
	var simulation = d3.forceSimulation()
	                   .force("link", d3.forceLink().id(function(d) {
					       return d.courseId;
					   }).strength(MOVE_STRENGTH))
					   .force("charge",d3.forceCollide().radius(NODE_BUFFER))
					   .force("center", d3.forceCenter(width / 2, height / 2));
	
	var links = [];
    var foreignAid = new Set(); // courses that have dependencies on courses in different departments
    function push_link(sc, tc, and_flag) {
        if(courses.find(c => c.courseId === tc.courseId) === undefined) {
            // do nothing
            foreignAid.add(sc.courseId);
            return;
        }
        links.push({source: sc.courseId,
                    target: tc.courseId,
                    and_flag: and_flag });
    }

    var isListIndicator = function(course) {
        return course === "and" || course === "or";
    }
    var push_links = function(sCourse, courselist, and_flag) {
        if(!Array.isArray(courselist)) {
            push_link(sCourse, courselist, and_flag);
            return;
        }
        courselist.forEach(function(course, index) {
            if(isListIndicator(course)) {
                push_links(sCourse,courselist[index+1],and_flag & course === "and"); 
            }
            else if(!Array.isArray(course) && course.hasOwnProperty("courseId")) {
                push_link(sCourse, course, and_flag);
            }
        });
    };
	var create_link_from_course_prereqs = function(course,and_flag) {
        if(!course.hasOwnProperty('prereq')) return;
		push_links(course,course.prereq,true);
	};
	
	courses.forEach(function(course) {
		create_link_from_course_prereqs(course,true);
	});
	
	var link = svg.selectAll(".link")
	              .data(links)
				  .enter()
				  .append("path")
				  .attr("class","link")
				  .attr("stroke", function(d) { return link_color;})
                  .attr("stroke-width",STROKE_WIDTH)
	
    var nodes = courses;
	var node = svg.selectAll(".node")
	              .data(nodes)
				  .enter().append("g");
	
	node.append("circle")
	    .attr("class", "node")
		.attr("r",NODE_RADIUS)
	    .on("mouseover", mouseOver(.2))
		.on("mouseout", mouseOut)
        .on("click",classClick)
        .style("fill","#ffffff")
        .style("stroke",function(d) { 
            return foreignAid.has(d.courseId) ? "red" : "black"; 
        });
	
	node.append("text")
	    .text(function(d) { return d.courseId.split(" ").pop(); })
        .attr("text-anchor","middle")
        .attr("style","pointer-events: none;")
	
	simulation.nodes(nodes).on("tick",ticked);
	simulation.force("link").links(links);
	
	function ticked() {
		link.attr("d", positionLink);
		node.attr("transform", positionNode);
	}
	
	function positionLink(d) {
        var dx = d.target.x - d.source.x,
            dy = d.target.y - d.source.y,
            //dr = Math.sqrt(dx * dx + dy * dy);
            dr = 0;
        return "M" + d.source.x + "," + d.source.y + "A" + dr + "," + dr + " 0 0,1 " + d.target.x + "," + d.target.y;
    }

    // move the node based on forces calculations
    function positionNode(d) {
        // keep the node within the boundaries of the svg
        if (d.x < 0) {
            d.x = 0
        };
        if (d.y < 0) {
            d.y = 0
        };
        if (d.x > width) {
            d.x = width
        };
        if (d.y > height) {
            d.y = height
        };
        return "translate(" + d.x + "," + d.y + ")";
    }
    /*

	// build a dictionary of nodes that are linked
    var linkedByIndex = {};
    links.forEach(function(d) {
        linkedByIndex[d.source.index + "," + d.target.index] = 1;
    });

    // check the dictionary to see if nodes are linked
    function isConnected(a, b) {
        return linkedByIndex[a.index + "," + b.index] || linkedByIndex[b.index + "," + a.index] || a.index == b.index;
    }
    */
    
    // 
    function convertPrereqsToList(prereqList,and_flag) {
        if(!Array.isArray(prereqList)) {
            return [{prereq: prereqList, and_flag: and_flag}];
        }
        else {
            var output = [];
            prereqList.forEach((p,i) => {
                if(isListIndicator(p)) {
                    output.push.apply(output,convertPrereqsToList(prereqList[i+1],and_flag & p === "and"))
                }
                else if(!Array.isArray(p) && p.hasOwnProperty("prereq")) {
                    output.push({prereq: p, and_flag: and_flag});
                }
            });
            return output;
        }
    }

    // returns a set of nodes reachable from root course (including root)
    //     and a dictionary indicating each reachable course's immediate dependencies
    // links should be a dictionary from course to a list of prereq's
    // e.g. dict[course] = [{target, and_flag}, {target, and_flag}, ...]
    function bfsPrereqs(course) {
        var visited = new Set();
        var linksSeen = {};
        var frontier = [{source: course, and_flag: true}];
        while(frontier.length > 0) {
            var curr = frontier.shift();
            //console.log("next item on frontier", curr);
            // if current node hasn't been visited
            if( !visited.has(curr.source.courseId) ) {
                visited.add(curr.source.courseId);
                // do nothing else if node has no more outgoing edges (i.e. no more prereq's)
                if(curr.source.hasOwnProperty("prereq")) {
                    // for each prereq, add to frontier and add link to map (courseId->prereqs)
                    // p has format: [{prereq, and_flag}, ...]
                    //console.log(convertPrereqsToList(curr.source.prereq))
                    convertPrereqsToList(curr.source.prereq).forEach((p) => {
                        frontier.push({source: p.prereq, and_flag: p.and_flag});
                        // initialize list of prereqs if source id hasn't been added already
                        //console.log("pushing link from",curr.source.courseId,"to",p.prereq.courseId);
                        if(curr.source.courseId in linksSeen) {
                            linksSeen[curr.source.courseId].push(p);
                        }
                        else {
                            linksSeen[curr.source.courseId] = [p];
                        }
                    })
                }
            }
        }
        return {visited: visited, linksSeen: linksSeen};
    }

    function searchForLink(link, linkDict) {
        //console.log(link,linkDict);
        if( link.source.courseId in linkDict ) {
            //console.log("hello");
            var found = -1;
            for(var i = 0; i < linkDict[link.source.courseId].length; i++) {
                //console.log(linkDict[link.source.courseId][i].prereq, link.target)
                if(linkDict[link.source.courseId][i].prereq.courseId === link.target.courseId) {
                    found = i;
                    break;
                }
            }
            return found;
        }
        return -1;
    }

    // fade nodes on hover
    function mouseOver(opacity) {
        return function(e, d) {
            var traverse = bfsPrereqs(d);
            //console.log("links seen:", traverse.linksSeen);

            // check all other nodes to see if they're connected
            // to this one. if so, keep the opacity at 1, otherwise
            // fade
            node.style("stroke-opacity", function(o) {
                //console.log(o.courseId, traverse.visited.has(o.courseId));
                var thisOpacity = traverse.visited.has(o.courseId) ? 1 : opacity;
                return thisOpacity;
            });
            node.style("fill-opacity", function(o) {
                var thisOpacity = traverse.visited.has(o.courseId) ? 1 : opacity;
                return thisOpacity;
            });

            // also style link accordingly
            link.style("stroke-opacity", function(o) {
                //console.log(o, traverse.linkSeen)
                var linkIndex = searchForLink(o,traverse.linksSeen);
                return linkIndex >= 0 ? 1 : opacity;
            });
            /*
            link.style("stroke", function(o){
                return o.source === d || o.target === d ? o.source.colour : "#ddd";
            });
            */
        };
    }

    function mouseOut() {
        node.style("stroke-opacity", 1);
        node.style("fill-opacity", 1);
        link.style("stroke-opacity", 1);
        link.style("stroke", link_color);
    }
	
	// function called when node is clicked
    function classClick(e,d) {
        console.log("clicked:",d);
        //window.open(d.link, '_blank');
        toggleCourse(d);
    };
}