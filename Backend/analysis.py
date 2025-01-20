import io
import pandas as pd
import matplotlib
import seaborn as sns
matplotlib.use('AGG')
import matplotlib.pyplot as plt


def preprocess_data(df_from_query):
    df_from_query['due_date'] = pd.to_datetime(df_from_query['due_date'], errors='coerce')
    df_from_query['creation_date'] = pd.to_datetime(df_from_query['creation_date'], errors='coerce')
    df_from_query['completed_date'] = pd.to_datetime(df_from_query['completed_date'], errors='coerce')
    df_from_query['status'].fillna('pending', inplace=True)
    df_from_query['completed_date'].fillna(pd.NaT, inplace=True)

    df_duplicates_removed = df_from_query.drop_duplicates(subset=df_from_query.columns.difference(['task_id', 'creation_date']))

    return df_duplicates_removed

def calculate_task_completion_time(df):
    df['completion_time'] = (df['completed_date'] - df['creation_date']).dt.total_seconds() / 3600  # hours
    df['completion_time'].fillna(0, inplace=True)
    return df

def identify_overdue_tasks(df):
    df['overdue'] = (df['completed_date'] > df['due_date']) | (df['status'] == 'pending')
    return df

def analyze_priority_distribution(df):
    priority_distribution = df['priority'].value_counts()
    return priority_distribution

def analyze_task_completion_time(df):
    completed_tasks = df[df['status'] == 'completed']
    task_completion_time = completed_tasks['completion_time']
    return task_completion_time

def generate_csv_report(df):
    csv_data = df.to_csv(index=False)
    return csv_data

def plot_completed_tasks_per_day(df):
    df['completed_day'] = df['completed_date'].dt.date
    completed_tasks_per_day = df.groupby('completed_day').size()

    fig=plt.figure(figsize=(10, 6))
    completed_tasks_per_day.plot(kind='bar', color='skyblue')
    plt.title('Number of Tasks Completed per Day')
    plt.xlabel('Date')
    plt.ylabel('Number of Tasks')
    plt.xticks(rotation=45)
    plt.tight_layout()
    img_buf = io.BytesIO()
    plt.savefig(img_buf, format='png')
    plt.close(fig)
    return img_buf

def plot_task_priority_distribution(df):
    priority_distribution = analyze_priority_distribution(df)

    fig=plt.figure(figsize=(8, 8))
    priority_distribution.plot(kind='pie', autopct='%1.1f%%', startangle=90, colors=['#ff9999','#66b3ff','#99ff99'])
    plt.title('Task Distribution by Priority')
    plt.ylabel('')
    plt.tight_layout()
    img_buf = io.BytesIO()
    plt.savefig(img_buf, format='png')
    plt.close(fig)
    return img_buf

def plot_completion_trends(df):
    df['completed_day'] = df['completed_date'].dt.date
    completed_tasks_per_day = df.groupby('completed_day').size()

    fig=plt.figure(figsize=(10, 6))
    completed_tasks_per_day.plot(kind='line', color='green', marker='o')
    plt.title('Task Completion Trends Over Time')
    plt.xlabel('Date')
    plt.ylabel('Number of Completed Tasks')
    plt.xticks(rotation=45)
    plt.tight_layout()
    img_buf = io.BytesIO()
    plt.savefig(img_buf, format='png')
    plt.close(fig)
    return img_buf

def plot_time_vs_priority(df):
    df['priority_code'] = df['priority'].map({'High': 3, 'Medium': 2, 'Low': 1})
    fig=plt.figure(figsize=(10, 6))
    sns.scatterplot(data=df, x='priority_code', y='completion_time', hue='priority', palette='coolwarm', s=100, edgecolor='black')
    plt.title('Time to Complete Tasks vs Priority')
    plt.xlabel('Priority')
    plt.ylabel('Completion Time (hours)')
    plt.tight_layout()
    img_buf = io.BytesIO()
    plt.savefig(img_buf, format='png')
    plt.close(fig)
    return img_buf