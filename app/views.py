from flask import render_template, flash, redirect, session, url_for, request, g, jsonify
from app import app, db
from .forms import TaskForm
from .models import Task
import json
from datetime import datetime
from config import LAMBDA, REFRESH_TIME

@app.route('/', methods=['GET', 'POST'])
@app.route('/list', methods=['GET', 'POST'])
def list():
    form = TaskForm()
    if form.validate_on_submit():
        task = Task(raw = form.task.data)
        db.session.add(task)
        db.session.commit()
        return redirect(url_for('list'))
    tasks = Task.active_tasks().all()
    return render_template('list.html',
        form = form,
        title = 'Todo List',
        tasks = tasks)

# @app.route('/')
@app.route('/pomodoro')
def pomodoro():
    pick = Task.pick_one()
    if pick is None:
        flash("Cannot pick one task")
        return redirect(url_for('list'))
    return render_template('pomodoro.html',
        title = 'Pomodoro',
        pick = pick)

@app.route('/complete/<int:task_id>')
def complete(task_id):
    task = Task.query.get(task_id)
    if task is None:
        flash("Task not found")
        return redirect(url_for('pomorodo'))
    task.completed = True
    task.completed_time = datetime.now()
    db.session.commit()
    return redirect(request.args.get('next') or url_for('list'))

@app.route('/add', methods=['POST'])
def add():
    task = Task(raw = request.form['task'])
    db.session.add(task)
    db.session.commit()
    # return jsonify({'task' : task})
    return jsonify({})

@app.route('/edit/<int:task_id>', methods = ['POST'])
def edit(task_id):
    task = Task.query.get(task_id)
    task.edit(request.form['task'])
    db.session.commit()
    display = {'todo' : task.todo,
         'estimated_time' : task.estimated_time,
         'raw' : task.raw }
    return jsonify(display)

@app.route('/notnow/<int:task_id>')
def notnow(task_id):
    task = Task.query.get(task_id)
    if datetime.now() - task.last_notnow > REFRESH_TIME:
        task.number_of_notnow = 0
    task.number_of_notnow +=1
    task.last_notnow = datetime.now()
    db.session.commit()
    return redirect(url_for('pomodoro'))

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500
