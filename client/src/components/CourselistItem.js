import { FaTimes } from 'react-icons/fa'

const CourselistItem = ({ course, onDelete, toggleCompleted }) => {
    return (
        <div className={`cli ${course.completed ? 'hello' : ''}`}>
            <h3>{course.courseId}
                <input type="checkbox" onClick={() => toggleCompleted(course.courseId)}/>
                <FaTimes
                    style={{color: 'red', cursor: 'pointer' }}
                    onClick={() => onDelete(course.courseId)}
                />
            </h3>
        </div>
    )
}

export default CourselistItem
