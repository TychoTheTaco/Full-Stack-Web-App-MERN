import React, { useState } from 'react'
import { Dropdown } from 'semantic-ui-react'
import $ from 'jquery'

const Header = ({departments,currDept,setCurrDept,getCourses}) => {
    //console.log("from header");
    //console.log(departments);
    const handleChange = (e, data) => {
        console.log("dropdown | clicked on " + e.target.innerText);
        setCurrDept(e.target.innerText);
        getCourses(data.value);
    }

    return (
        <div id="hDiv">
            <Dropdown
                id="DeptDrop"
                placeholder="Select Department"
                fluid
                search
                selection={false}
                value={currDept}
                options={departments}
                onChange={handleChange}
            />
        </div>
    )
    /*
    return (
        <div id="hDiv">
            <CDropdown title="Select movie" items={departments} />
        </div>
    )
    */
}

export default Header