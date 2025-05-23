
from datetime import datetime
from flask import redirect,url_for,render_template,request

#from app.logic import CATEGORY_TYPE_MAP, compute_productivity_stats, generate_charts, generate_schedule, optimise_task_schedule, read_data, read_data_csv
from app.logic import (
    CATEGORY_TYPE_MAP, 
    ChartsManipulations,
    podomoroTechnique,
    batchRecommendation,
    taskManipulations,
)

from . import app, dir_path

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/tasks')
def tasks():
    return render_template('tasks.html')


@app.route('/dashboard', methods=['POST'])
def dashboard():
    tasks = request.form.getlist('task')
    categories = request.form.getlist('category')
    start_times = request.form.getlist('start_time')
    end_times = request.form.getlist('end_time')
    energy = request.form['energy']
    
    ChartsManipulationsOPS = ChartsManipulations()
    taskManipulationsOPS = taskManipulations()

    # Check if user wants automatic time blocking
    use_time_blocking = request.form.get('use_time_blocking', 'off') == 'on'
    
    if use_time_blocking:
        # Generate optimized schedule
        schedule = taskManipulationsOPS.generate_time_blocked_schedule(tasks, categories, start_times, end_times, energy)
    else:
        # Use the original schedule as provided by user
        schedule = ChartsManipulationsOPS.generate_schedule(tasks, categories, start_times, end_times, energy)
    
    df = ChartsManipulationsOPS.read_data(schedule)
    ChartsManipulationsOPS.generate_charts(df)
    
    stats = ChartsManipulationsOPS.compute_productivity_stats(df)
    return render_template('dashboard.html', stats=stats)

@app.route('/optimise', methods=['POST'])
def optimise():
    """Route for optimizing an existing schedule"""
    tasks = request.form.getlist('task')
    categories = request.form.getlist('category')
    start_times = request.form.getlist('start_time')
    end_times = request.form.getlist('end_time')
    energy = request.form['energy']
    
    # Parse times to calculate durations
    parsed_start_times = [datetime.strptime(t, "%H:%M") for t in start_times]
    parsed_end_times = [datetime.strptime(t, "%H:%M") for t in end_times]
    durations = [(parsed_end_times[i] - parsed_start_times[i]).total_seconds() / 60 for i in range(len(tasks))]
    
    # Get overall schedule start and end
    overall_start = min(parsed_start_times)
    overall_end = max(parsed_end_times)
    
    ChartsManipulationsOPS = ChartsManipulations()
    taskManipulationsOPS = taskManipulations()

    # optimise the schedule
    optimised_blocks = taskManipulationsOPS.optimise_task_schedule(tasks, categories, durations, overall_start, overall_end, energy)
    
    # Prepend energy information
    schedule = [{'energy': energy}]
    schedule.extend(optimised_blocks)
    
    df =ChartsManipulationsOPS.read_data(schedule)
    ChartsManipulationsOPS.generate_charts(df)
    
    stats = ChartsManipulationsOPS.compute_productivity_stats(df)
    return render_template('dashboard.html', stats=stats, is_optimised=True)



@app.route('/pomodoro', methods=['POST'])
def pomodoro_schedule():
    """Route for generating a Pomodoro-based schedule"""
    tasks = request.form.getlist('task')
    categories = request.form.getlist('category')
    start_times = request.form.getlist('start_time')
    end_times = request.form.getlist('end_time')
    energy = request.form['energy']
    
    # Get Pomodoro settings from form
    pomodoro_settings = {
        'focus_duration': int(request.form.get('focus_duration', 25)),
        'short_break': int(request.form.get('short_break', 5)),
        'long_break': int(request.form.get('long_break', 15)),
        'sessions_before_long_break': int(request.form.get('sessions_before_long_break', 4))
    }
    podomoroTechniqueOPS = podomoroTechnique(tasks, categories,start_times, end_times, energy, pomodoro_settings) 
    # Generate Pomodoro schedule
    schedule = podomoroTechniqueOPS.generate_daily_schedule_with_pomodoro()


    ChartsManipulationsOPS = ChartsManipulations()
    batchRecommendationOPS = batchRecommendation(tasks, categories)

    
    df = ChartsManipulationsOPS.read_data(schedule)
    ChartsManipulationsOPS.generate_charts(df)
    
    stats = ChartsManipulationsOPS.compute_productivity_stats(df)
    
    # Parse times to calculate durations for batching recommendations
    parsed_start_times = [datetime.strptime(t, "%H:%M") for t in start_times]
    parsed_end_times = [datetime.strptime(t, "%H:%M") for t in end_times]
    durations = [(parsed_end_times[i] - parsed_start_times[i]).total_seconds() / 60 for i in range(len(tasks))]
    
    # Generate batching recommendations
    batching_recommendations = batchRecommendationOPS.generate_task_batching_recommendations(durations)
    
    return render_template(
        'dashboard.html', 
        stats=stats, 
        is_pomodoro=True,
        batching_recommendations=batching_recommendations
    )


@app.route('/pomodoro_settings', methods=['POST'])
def pomodoro_settings():
    """Route for displaying Pomodoro settings form"""
    return render_template('pomodoro_settings.html')

