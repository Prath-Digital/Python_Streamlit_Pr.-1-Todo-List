import streamlit as st
import json
import os
from datetime import datetime
from typing import List, Dict, Any

DATA_FILE = "tasks.json"


# Task data structure
def create_task(text: str, priority: str = "Medium") -> Dict[str, Any]:
    return {
        "id": datetime.now().timestamp(),
        "task": text,
        "done": False,
        "priority": priority,
        "created_at": datetime.now().isoformat(),
        "completed_at": None,
    }


# Load tasks
def load_tasks() -> List[Dict[str, Any]]:
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                tasks = json.load(f)
                # Ensure backward compatibility
                for task in tasks:
                    if "id" not in task:
                        task["id"] = datetime.now().timestamp()
                    if "priority" not in task:
                        task["priority"] = "Medium"
                    if "created_at" not in task:
                        task["created_at"] = datetime.now().isoformat()
                    if "completed_at" not in task:
                        task["completed_at"] = None
                return tasks
        except (json.JSONDecodeError, FileNotFoundError):
            return []
    return []


# Save tasks
def save_tasks(tasks: List[Dict[str, Any]]) -> None:
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(tasks, f, indent=2, ensure_ascii=False)
    except Exception as e:
        st.error(f"Error saving tasks: {e}")


# Toggle task completion
def toggle_task_completion(task_id: float) -> None:
    for task in st.session_state.tasks:
        if task["id"] == task_id:
            task["done"] = not task["done"]
            task["completed_at"] = datetime.now().isoformat() if task["done"] else None
            break
    save_tasks(st.session_state.tasks)


# Delete task
def delete_task(task_id: float) -> None:
    st.session_state.tasks = [
        task for task in st.session_state.tasks if task["id"] != task_id
    ]
    save_tasks(st.session_state.tasks)


# Edit task
def edit_task(task_id: float, new_text: str, new_priority: str) -> None:
    for task in st.session_state.tasks:
        if task["id"] == task_id:
            task["task"] = new_text
            task["priority"] = new_priority
            break
    save_tasks(st.session_state.tasks)


# Get priority color and icon
def get_priority_style(priority: str) -> tuple:
    styles = {
        "High": ("🔴", "#ff4b4b"),
        "Medium": ("🟡", "#ffa500"),
        "Low": ("🟢", "#00b050"),
    }
    return styles.get(priority, ("🟡", "#ffa500"))


# Sort tasks
def sort_tasks(tasks: List[Dict[str, Any]], sort_by: str) -> List[Dict[str, Any]]:
    if sort_by == "Priority":
        priority_order = {"High": 0, "Medium": 1, "Low": 2}
        return sorted(
            tasks, key=lambda x: (x["done"], priority_order.get(x["priority"], 1))
        )
    elif sort_by == "Created Date":
        return sorted(tasks, key=lambda x: (x["done"], x["created_at"]))
    elif sort_by == "Alphabetical":
        return sorted(tasks, key=lambda x: (x["done"], x["task"].lower()))
    return tasks


# Initialize session state
if "tasks" not in st.session_state:
    st.session_state.tasks = load_tasks()

if "show_completed" not in st.session_state:
    st.session_state.show_completed = True

if "edit_mode" not in st.session_state:
    st.session_state.edit_mode = {}

# Page configuration
st.set_page_config(
    page_title="Enhanced To-Do List",
    page_icon="./assets/logo.png",
    layout="centered",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown(
    """
<style>
.task-container {
    border-radius: 10px;
    padding: 1rem;
    margin: 0.5rem 0;
    border-left: 4px solid;
}
.high-priority { border-left-color: #ff4b4b; background-color: #fff5f5; }
.medium-priority { border-left-color: #ffa500; background-color: #fffbf0; }
.low-priority { border-left-color: #00b050; background-color: #f0fff4; }
.completed-task { opacity: 0.6; }
.stats-card {
    background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 1rem;
    border-radius: 10px;
    text-align: center;
}
</style>
""",
    unsafe_allow_html=True,
)

# Header
st.title("✅ Enhanced To-Do List")
st.markdown("*Stay organized and productive with priority management*")

# Sidebar
with st.sidebar:
    st.header("📊 Dashboard")

    # Statistics
    total_tasks = len(st.session_state.tasks)
    completed_tasks = sum(1 for task in st.session_state.tasks if task["done"])
    pending_tasks = total_tasks - completed_tasks

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total", total_tasks)
    with col2:
        st.metric("Pending", pending_tasks)
    with col3:
        st.metric("Done", completed_tasks)

    if total_tasks > 0:
        completion_rate = (completed_tasks / total_tasks) * 100
        st.progress(completion_rate / 100)
        st.caption(f"Completion Rate: {completion_rate:.1f}%")

    st.divider()

    # Filters and sorting
    st.header("🔧 Options")
    sort_option = st.selectbox("Sort by", ["Priority", "Created Date", "Alphabetical"])
    st.session_state.show_completed = st.checkbox(
        "Show completed tasks", value=st.session_state.show_completed
    )

    # Clear completed tasks
    if completed_tasks > 0:
        if st.button("🗑️ Clear Completed", use_container_width=True):
            st.session_state.tasks = [
                task for task in st.session_state.tasks if not task["done"]
            ]
            save_tasks(st.session_state.tasks)
            st.rerun()

    # Export/Import
    st.divider()
    st.header("💾 Data Management")

    if st.button("📥 Export Tasks", use_container_width=True):
        if st.session_state.tasks:
            st.download_button(
                "Download JSON",
                data=json.dumps(st.session_state.tasks, indent=2),
                file_name=f"tasks_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
            )

    uploaded_file = st.file_uploader("📤 Import Tasks", type="json")
    if uploaded_file:
        try:
            imported_tasks = json.load(uploaded_file)
            if st.button("Confirm Import"):
                st.session_state.tasks.extend(imported_tasks)
                save_tasks(st.session_state.tasks)
                st.success(f"Imported {len(imported_tasks)} tasks!")
                st.rerun()
        except json.JSONDecodeError:
            st.error("Invalid JSON file")

# Main content
# Add new task section
st.header("➕ Add New Task")
with st.form("add_task_form", clear_on_submit=True):
    col1, col2 = st.columns([3, 1])
    with col1:
        new_task = st.text_input(
            "Task description", placeholder="Enter your task here..."
        )
    with col2:
        priority = st.selectbox("Priority", ["High", "Medium", "Low"], index=1)

    submitted = st.form_submit_button("Add Task", use_container_width=True)

    if submitted and new_task.strip():
        new_task_obj = create_task(new_task.strip(), priority)
        st.session_state.tasks.append(new_task_obj)
        save_tasks(st.session_state.tasks)
        st.success(f"Added task: {new_task}")
        st.rerun()

# Display tasks
st.header("📋 Your Tasks")

if st.session_state.tasks:
    # Filter tasks based on show_completed setting
    filtered_tasks = st.session_state.tasks
    if not st.session_state.show_completed:
        filtered_tasks = [task for task in st.session_state.tasks if not task["done"]]

    # Sort tasks
    sorted_tasks = sort_tasks(filtered_tasks, sort_option)

    if not sorted_tasks:
        st.info("No tasks to display with current filters.")
    else:
        for task in sorted_tasks:
            task_id = task["id"]
            priority_icon, priority_color = get_priority_style(task["priority"])

            # Task container
            with st.container():
                if task["done"]:
                    container_class = "completed-task"
                else:
                    priority_class = f"{task['priority'].lower()}-priority"
                    container_class = f"task-container {priority_class}"

                col1, col2, col3, col4 = st.columns([0.1, 0.7, 0.1, 0.1])

                # Checkbox
                with col1:
                    is_done = st.checkbox(
                        "",
                        value=task["done"],
                        key=f"check_{task_id}",
                        label_visibility="collapsed",
                    )
                    if is_done != task["done"]:
                        toggle_task_completion(task_id)
                        st.rerun()

                # Task content
                with col2:
                    if (
                        task_id in st.session_state.edit_mode
                        and st.session_state.edit_mode[task_id]
                    ):
                        # Edit mode
                        edit_col1, edit_col2 = st.columns([3, 1])
                        with edit_col1:
                            edited_text = st.text_input(
                                "",
                                value=task["task"],
                                key=f"edit_text_{task_id}",
                                label_visibility="collapsed",
                            )
                        with edit_col2:
                            edited_priority = st.selectbox(
                                "",
                                ["High", "Medium", "Low"],
                                index=["High", "Medium", "Low"].index(task["priority"]),
                                key=f"edit_priority_{task_id}",
                                label_visibility="collapsed",
                            )

                        # Save/Cancel buttons
                        save_col, cancel_col = st.columns(2)
                        with save_col:
                            if st.button("💾", key=f"save_{task_id}", help="Save"):
                                edit_task(task_id, edited_text, edited_priority)
                                st.session_state.edit_mode[task_id] = False
                                st.rerun()
                        with cancel_col:
                            if st.button("❌", key=f"cancel_{task_id}", help="Cancel"):
                                st.session_state.edit_mode[task_id] = False
                                st.rerun()
                    else:
                        # Display mode
                        task_text = task["task"]
                        if task["done"]:
                            st.markdown(
                                f"{priority_icon} ~~{task_text}~~ *({task['priority']} priority)*"
                            )
                            if task.get("completed_at"):
                                completed_date = datetime.fromisoformat(
                                    task["completed_at"]
                                ).strftime("%m/%d/%Y %H:%M")
                                st.caption(f"Completed on {completed_date}")
                        else:
                            st.markdown(
                                f"{priority_icon} **{task_text}** *({task['priority']} priority)*"
                            )
                            created_date = datetime.fromisoformat(
                                task["created_at"]
                            ).strftime("%m/%d/%Y %H:%M")
                            st.caption(f"Created on {created_date}")

                # Edit button
                with col3:
                    if not task["done"]:
                        if st.button("✏️", key=f"edit_{task_id}", help="Edit task"):
                            st.session_state.edit_mode[task_id] = True
                            st.rerun()

                # Delete button
                with col4:
                    if st.button("🗑️", key=f"delete_{task_id}", help="Delete task"):
                        delete_task(task_id)
                        if task_id in st.session_state.edit_mode:
                            del st.session_state.edit_mode[task_id]
                        st.rerun()

                st.divider()

else:
    st.info("🎉 No tasks yet! Add your first task above to get started.")

# Footer
st.markdown("*Made with ❤️ using Streamlit*")
