from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
from huggingface_hub import snapshot_download
from jwt_utils import get_jwt_data
from chatbot import prever_intencao
from graphs import (
    accumulated_progress,
    activity_performance,
    average_performance_by_course,
    completed_steps_within_time_rate,
    course_completion_report,
    course_popularity,
    course_students,
    favorited_courses,
    incomplete_steps_analysis,
    individual_progress,
    performance_benchmark_report,
    user_activity_over_week,
    user_gender_distribution,
)
from queries import ChatbotQuery


app = FastAPI()
snapshot_download('neuralmind/bert-base-portuguese-cased', repo_type='model')


@app.get("/graph/{graph}/{institution_id}")
async def get_graph(request: Request, graph: str, institution_id: str):
    if graph == "course_students":
        data = course_students(institution_id)
    elif graph == "accumulated_students":
        data = accumulated_progress(institution_id)
    elif graph == "course_popularity":
        data = course_popularity(institution_id)
    elif graph == "individual_progress":
        data = individual_progress(institution_id)
    elif graph == "average_performance_by_course":
        data = average_performance_by_course(institution_id)
    elif graph == "performance_benchmark_report":
        data = performance_benchmark_report(institution_id)
    elif graph == "user_gender_distribution":
        data = user_gender_distribution(institution_id)
    elif graph == "user_activity_over_week":
        data = user_activity_over_week(institution_id)
    elif graph == "course_completion_report":
        data = course_completion_report(institution_id)
    elif graph == "favorited_courses":
        data = favorited_courses(institution_id)
    elif graph == "incomplete_steps_analysis":
        data = incomplete_steps_analysis(institution_id)
    elif graph == "activity_performance":
        data = activity_performance(institution_id)
    elif graph == "completed_steps_within_time_rate":
        data = completed_steps_within_time_rate(institution_id)
    else:
        return {"error": "Graph not found"}

    return PlainTextResponse(data)


@app.post("/chatbot")
async def get_chatbot_response(request: Request, query: ChatbotQuery):
    data = get_jwt_data(request)
    user_email = data.get("email")
    return prever_intencao(query.user_message, user_email, query.context)
