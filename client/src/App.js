import React from 'react'
import {useState} from 'react'
//import ForceGraph from 'force-graph'
import VisReact from './components/VisReact'
import Header from './components/Header'
import './App.css'

function retrieveDepartments() {
  let response = fetch("http://localhost:5000/server/departments")
      .then((response) => response.json())
      .then((data) => {
        // add text key
        for(var key in data) {
          data[key].text = data[key].deptName;
        }
      });
  return response.json();
}

function App() {
  const [courses, setCourses] = useState("");
  const [departments, setDepartments] = useState("");
  const [currDept, setCurrDept] = useState("");

  const getCourses = (deptID) => {
    fetch("http://localhost:5000/server/departments/" + deptID + "/courses")
      .then((response) => response.json())
      .then((data) => {
        //setCourses()
        console.log("showing courses");
        console.log(data);
      });
  }

  const getDepartments = () => {
    fetch("http://localhost:5000/server/departments")
      .then((response) => response.json())
      .then((data) => {
        // add text key
        for(var key in data) {
          data[key].text = data[key].deptName;
        }
        setDepartments(data);
        //console.log("showing data and depts");
        //console.log(departments);
      });
    //console.log(departments);
  }

  return (
    <div className='horiz-flex'>
      <div className='vert-flex'>
        <Header depts={departments, currDept}/>
        <button onClick={() => {
          console.log("Clicked!");
          getDepartments();
          console.log(departments);
        }}>Get Departments</button>
        <div className = 'vis-react'>
          <VisReact/>
        </div>
      </div>
      <div>
        Hello World
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
