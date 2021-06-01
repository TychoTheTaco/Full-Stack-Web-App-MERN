import React from 'react'
import {useState,useEffect,useRef} from 'react'
import _ from 'underscore'

import Header from './components/Header'
import {generateChart} from './components/coursechart'
import {generateChart2} from './components/newcc'
import Sidebar from './components/Sidebar'

import chartinfo from './components/hkn_chartinfo.json'
import './App.css'
import $ from 'jquery'
import Courselist from './components/Courselist'


function App() {
  //const [courses, setCourses] = useState([]);
  const [courselist, setCourselist] = useState([]);
  const [departments, setDepartments] = useState([]);
  const [currDept, setCurrDept] = useState("");
  const [schedule, setSchedule] = useState([]);
  const graphContainer = useRef(null);

  useEffect(() => {
    getDepartments();
    
    //console.log("use effect");
    //generateChart(chartinfo, $("#chart"), 1);
  },[])

  useEffect(() => {
    courselist.sort(compareCourses);
  },[courselist])

  const getDepartments = () => {
    fetch("http://localhost:5000/server/departments")
      .then((response) => response.json())
      .then((data) => {
        // remove duplicate departments with the same deptId
        data = _.uniq(data, false, function(d, k, v) {return d.deptId});
        // add the 'text' property to each dept
        for(var key in data) {
          data[key].text = data[key].deptName;
          data[key].key = data[key].deptId;
          data[key].value = data[key].deptId;
          delete data[key].deptId;
          delete data[key].deptName;
        }
        // sort departments by deptId
        data.sort((a,b) => (a.key > b.key) ? 1 : -1);
        setDepartments(data);
      });
  }

  const getCourses = (deptID) => {
    fetch("http://localhost:5000/server/departments/" + deptID + "/courses")
      .then((response) => response.json())
      .then((data) => {
        console.log("got courses for " + deptID)
        console.log(data);
        for(var course in data) {
          data[course].completed = false;
        }
        data.sort(compareCourses);
        //setCourselist(data);
        console.log("data:",data);
        data = data.filter((course) => getCourseNumSeries(course.courseId).cnum < 200);
        console.log("data filtered:", data);
        generateChart2(data,$("#chart"),toggleCourse);
      });
  }

  // ~~~~~~~~~~~~~~~~~~~~~ COURSELIST RELATED ~~~~~~~~~~~~~~~~~~~~~ //

  // retrieves the courseId's series, number, and subseries (e.g. E10A)
  // assumes course number has the following format: [a-zA-Z]*[0-9]+[a-zA-Z]*
  var getCourseNumSeries = function(cID) {
    var lastword = cID.substring(cID.lastIndexOf(" ") + 1);
    var wordslice = lastword.match(/(?<cseries>[a-zA-Z]*)(?<cnum>[0-9]+)(?<csubseries>[a-zA-Z]*)/)
    //console.log("getting coursenumseries for " + cID)
    //console.log(lastword)
    //console.log(wordslice)
    return {
      cseries: wordslice.groups.cseries,
      cnum: parseInt(wordslice.groups.cnum),
      csubseries: wordslice.groups.csubseries
    }
  }

  // sorting function for courses by courseId
  var compareCourses = function( c1, c2 ) {
    if(c1.deptId !== c2.deptId) {
      return c1.deptId.localeCompare(c2.deptId)
    }
    else {
      var c1NS = getCourseNumSeries(c1.courseId);
      var c2NS = getCourseNumSeries(c2.courseId);
      if(c1NS.cnum != c2NS.cnum) {
        return c1NS.cnum - c2NS.cnum;
      }
      else if (c1NS.cseries != c2NS.cseries) {
        return c1NS.cseries.localeCompare(c2NS.cseries);
      }
      return c1NS.csubseries.localeCompare(c2NS.csubseries);
    }
  }

  // sorting function for courses by courseId
  var compareCourseIDs = function( cID1, cID2 ) {
    var getDeptID = function(cID) {
      return cID.substring(0,cID.lastIndexOf(" "));
    }
    if(getDeptID(cID1) !== getDeptID(cID2)) {
      return getDeptID(cID1).localeCompare(getDeptID(cID2));
    }
    else {
      var c1NS = getCourseNumSeries(cID1);
      var c2NS = getCourseNumSeries(cID2);
      if(c1NS.cnum != c2NS.cnum) {
        return c1NS.cnum - c2NS.cnum;
      }
      else if (c1NS.cseries != c2NS.cseries) {
        return c1NS.cseries.localeCompare(c2NS.cseries);
      }
      return c1NS.csubseries.localeCompare(c2NS.csubseries);
    }
  }

  const toggleCourse = (course) => {
    //setCourselist((courselist) => 
    console.log("function toggleCourse");
    if(courselist.map(function(c) {return c.courseId}).indexOf(course.courseId) > -1) {
      console.log("deleting course");
      deleteCourse(course.courseId);
    }
    else {
      console.log("adding course");
      setCourselist(courselist => [...courselist, course]);
    }
    
  }

  // Delete course from courselist
  const deleteCourse = (id) => {
    //console.log('delete task',id)
    //console.log(getCourseNumSeries(id))
    setCourselist(courselist.filter((course) => course.courseId !== id))
  }

  // Toggle reminder
  const toggleCompleted = (id) => {
    console.log(id)
    setCourselist(courselist.map((course) => course.courseId === id ? { ...course, completed: !course.completed} : course))
    console.log(courselist)
  }

// format for fetch
// http://localhost:5000/server/schedule?required=COMPSCI%20111%2C%20COMPSCI%20112%2C%20ART%2011A
// (comma separated list of course ids)
// returns list of lists of course ids
  const getSchedule = () => {
    var url = "http://localhost:5000/server/schedule?required=";
    console.log("courselist before schedule:", courselist)
    url += courselist.join("%2C").replace(" ","%20")
    fetch(url)
      .then((response) => response.json())
      .then((data) => {
        setSchedule(data);
      });
  }

  return (
    <div className='horiz-flex'>
      <div className='vert-flex'>
        <Header departments={departments} currDept={currDept} setCurrDept={setCurrDept} getCourses={getCourses}/>
        <p>Selected department: {currDept}</p>
        <div id="chart" ref={graphContainer}></div>
      </div>
      <div>
        <button onClick={getSchedule}>get schedule</button>
        Hello world
        <Courselist courses={courselist} onDelete={deleteCourse} toggleCompleted={toggleCompleted}/>
        <div className='schedule'>
          {schedule.map((quarter) => (
            <h1>{quarter}</h1>
          ))}
        </div>
      </div>
    </div>
  );
}

// TODO: Switch to https://github.com/palmerhq/the-platform#stylesheet when it will be stable
const styleLink = document.createElement("link");
styleLink.rel = "stylesheet";
styleLink.href = "https://cdn.jsdelivr.net/npm/semantic-ui/dist/semantic.min.css";
document.head.appendChild(styleLink);

export default App;