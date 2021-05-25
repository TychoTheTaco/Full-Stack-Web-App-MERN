import React from 'react'
import { Dropdown } from 'semantic-ui-react'

const Header = ({ departments, currDept }) => {
    return (
        <div>
            <Dropdown
                placeholder='Select Department'
                fluid
                search
                selection
                options={departments}
                onChange={ function(value, text, $selectedItem) {
                    console.log("WE GOT HERE");
                    console.log(this.dropdown('get value'));
                }}
            />
        </div>
    )
}

export default Header