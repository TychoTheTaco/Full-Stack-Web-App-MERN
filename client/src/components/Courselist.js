import CourselistItem from './CourselistItem'

const Courselist = ({ courses, onDelete, toggleCompleted }) => {
    return (
        <>
            {courses.map((course) => (
                <CourselistItem course={course} onDelete={onDelete} toggleCompleted={toggleCompleted}/>
            ))}
        </>
    )
}

export default Courselist
