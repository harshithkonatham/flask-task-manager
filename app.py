from flask import Flask, render_template, request, redirect

app = Flask(__name__)

# In-memory list to store tasks (real-world: use a database later)
tasks = []

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Add new task
        task = request.form.get('task')
        if task:
            tasks.append(task)
        # Delete task if requested
        delete_index = request.form.get('delete')
        if delete_index:
            del tasks[int(delete_index)]
        return redirect('/')
    return render_template('index.html', tasks=tasks)

if __name__ == '__main__':
    app.run(debug=True)