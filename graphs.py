import base64
from io import BytesIO
import matplotlib.pyplot as plt
import pandas as pd
import pymysql
import seaborn as sns
import numpy as np
from os import environ


def connect_to_db(host, port, user, password, db_name):
    conn = pymysql.connect(host=host, port=port, user=user, password=password, database=db_name, ssl={"teste": True})
    return conn


sns.set(style="whitegrid")


def course_students(institution_id):
    conn = connect_to_db(
        host=environ.get("DB_HOST"),
        port=int(environ.get("DB_PORT")),
        user=environ.get("DB_USER"),
        password=environ.get("DB_PASSWORD"),
        db_name=environ.get("DB_NAME"),
    )
    query_courses = """
    SELECT 
        c.name AS Curso, 
        i.name AS Instituicao,
        COALESCE(COUNT(e.userId), 0) AS Total_Inscritos
    FROM Courses c
    LEFT JOIN Institutions i ON c.institutionId = i.id
    LEFT JOIN Enrollments e ON c.id = e.courseId
    WHERE i.id = %s
    GROUP BY c.id, c.name, i.name
    ORDER BY Total_Inscritos DESC;
    """
    df_courses = pd.read_sql(query_courses, conn, params=[institution_id])

    df_courses["Total_Inscritos"] = df_courses["Total_Inscritos"].astype(int)

    num_cursos = len(df_courses)
    palette = sns.color_palette("husl", num_cursos)  # Gera cores únicas

    plt.figure(figsize=(12, 6))
    ax = sns.barplot(x="Total_Inscritos", y="Curso", data=df_courses, palette=palette)

    plt.title("Total de Docentes Inscritos por Curso", fontsize=14)
    plt.xlabel("Total de Inscritos", fontsize=12)
    plt.ylabel("Curso", fontsize=12)
    plt.xticks(fontsize=10)
    plt.yticks(fontsize=10)
    plt.grid(axis="x", linestyle="--", alpha=0.7)

    plt.tight_layout()
    print(df_courses)
    bio = BytesIO()
    plt.savefig(bio, format="png")
    bio.seek(0)
    return base64.b64encode(bio.read())


def accumulated_progress(institution_id):
    conn = connect_to_db(
        host=environ.get("DB_HOST"),
        port=int(environ.get("DB_PORT")),
        user=environ.get("DB_USER"),
        password=environ.get("DB_PASSWORD"),
        db_name=environ.get("DB_NAME"),
    )
    query_progress = """
    SELECT 
        U.id AS Usuario_ID,
        U.name AS Nome,
        C.id AS Curso_ID,
        C.name AS Curso,
        E.enrollmentDate AS Data_Inscricao,
        UP.progressDate AS Data_Progresso,
        I.id AS Instituicao_ID,
        I.name AS Instituicao
    FROM Users U
    JOIN Enrollments E ON U.id = E.userId
    JOIN Courses C ON E.courseId = C.id
    JOIN Institutions I ON C.institutionId = I.id
    LEFT JOIN UserProgress UP ON E.id = UP.enrollmentId
    WHERE I.id = %s  -- 🚀 Substituir pelo ID da instituição desejada
    ORDER BY UP.progressDate;
    """

    df_progress = pd.read_sql(query_progress, conn, params=[institution_id])

    df_progress = df_progress[df_progress["Instituicao_ID"] == 3]

    df_progress["Data_Progresso"] = pd.to_datetime(df_progress["Data_Progresso"], errors="coerce").dt.strftime(
        "%d/%m/%Y"
    )

    df_progress_grouped = df_progress.groupby(["Data_Progresso", "Nome"]).size().unstack(fill_value=0).cumsum()

    plt.figure(figsize=(16, 8))
    df_progress_grouped.plot(kind="bar", stacked=True, colormap="Set3", ax=plt.gca())

    plt.title("Progresso Acumulado dos Usuários ao Longo do Tempo", fontsize=16)
    plt.xlabel("Data de Progresso", fontsize=14)
    plt.ylabel("Progresso Acumulado", fontsize=14)
    plt.xticks(rotation=90, fontsize=10)

    plt.legend(title="Usuários", bbox_to_anchor=(1.05, 1), loc="upper left")
    plt.grid(axis="y", linestyle="--", alpha=0.7)

    plt.tight_layout()
    bio = BytesIO()
    plt.savefig(bio, format="png")
    bio.seek(0)
    return base64.b64encode(bio.read())


def course_popularity(institution_id):
    conn = connect_to_db(
        host=environ.get("DB_HOST"),
        port=int(environ.get("DB_PORT")),
        user=environ.get("DB_USER"),
        password=environ.get("DB_PASSWORD"),
        db_name=environ.get("DB_NAME"),
    )
    query_popularity = """
    SELECT 
        c.name AS Curso, 
        COUNT(DISTINCT e.userId) AS Total_Finalizados
    FROM Courses c
    LEFT JOIN Enrollments e ON c.id = e.courseId
    LEFT JOIN UserProgress up ON e.id = up.enrollmentId
    JOIN Institutions i ON c.institutionId = i.id
    WHERE i.id = %s
    GROUP BY c.id, c.name;
    """

    df_popularity = pd.read_sql(query_popularity, conn, params=[institution_id])

    df_popularity["Total_Finalizados"] = df_popularity["Total_Finalizados"].fillna(0).astype(int)

    if df_popularity["Total_Finalizados"].sum() == 0:
        df_popularity.loc[len(df_popularity)] = ["Nenhum Curso Finalizado", 1]

    plt.figure(figsize=(8, 8))
    plt.pie(
        df_popularity["Total_Finalizados"],
        labels=df_popularity["Curso"],
        autopct="%1.1f%%",
        colors=sns.color_palette("coolwarm", len(df_popularity)),
        startangle=140,
    )
    plt.title("Popularidade dos Cursos")
    bio = BytesIO()
    plt.savefig(bio, format="png")
    bio.seek(0)
    return base64.b64encode(bio.read())


def individual_progress(institution_id):
    conn = connect_to_db(
        host=environ.get("DB_HOST"),
        port=int(environ.get("DB_PORT")),
        user=environ.get("DB_USER"),
        password=environ.get("DB_PASSWORD"),
        db_name=environ.get("DB_NAME"),
    )
    query_individual_progress = """
    SELECT 
        u.name AS Nome, 
        c.name AS Curso, 
        COUNT(up.stepId) AS Progresso
    FROM Enrollments e
    JOIN Users u ON e.userId = u.id
    JOIN Courses c ON e.courseId = c.id
    LEFT JOIN UserProgress up ON e.id = up.enrollmentId
    WHERE c.institutionId = %s
    GROUP BY u.id, u.name, c.id, c.name
    ORDER BY u.name, c.name
    """

    df_individual_progress = pd.read_sql(query_individual_progress, conn, params=[institution_id])

    df_individual_progress["Progresso"] = df_individual_progress["Progresso"].astype(int)

    plt.figure(figsize=(12, 8))
    sns.barplot(x="Progresso", y="Nome", hue="Curso", data=df_individual_progress, palette="coolwarm")
    plt.title("Progresso Individual dos Usuários")
    plt.xlabel("Progresso (Quantidade de Etapas Completas)")
    plt.ylabel("Usuários")
    plt.legend(title="Curso", bbox_to_anchor=(1.05, 1), loc="upper left")
    plt.tight_layout()
    bio = BytesIO()
    plt.savefig(bio, format="png")
    bio.seek(0)
    return base64.b64encode(bio.read())


def average_performance_by_course(institution_id):
    conn = connect_to_db(
        host=environ.get("DB_HOST"),
        port=int(environ.get("DB_PORT")),
        user=environ.get("DB_USER"),
        password=environ.get("DB_PASSWORD"),
        db_name=environ.get("DB_NAME"),
    )
    query_benchmarking = """
    SELECT 
        c.name AS Curso,
        (COUNT(up.stepId) / (SELECT COUNT(s.id) FROM Steps s WHERE s.courseId = c.id)) * 100 AS Media_Progresso
    FROM Courses c
    LEFT JOIN Enrollments e ON c.id = e.courseId
    LEFT JOIN UserProgress up ON e.id = up.enrollmentId
    WHERE c.institutionId = %s
    GROUP BY c.id, c.name
    ORDER BY Media_Progresso DESC;
    """

    df_benchmarking = pd.read_sql(query_benchmarking, conn, params=[institution_id])

    plt.figure(figsize=(10, 6))
    sns.barplot(x="Media_Progresso", y="Curso", data=df_benchmarking, palette="viridis")
    plt.title("Benchmarking de Progresso por Curso (%)")
    plt.xlabel("Progresso Médio (%)")
    plt.ylabel("Curso")
    plt.xlim(0, 100)
    bio = BytesIO()
    plt.savefig(bio, format="png")
    bio.seek(0)
    return base64.b64encode(bio.read())


def performance_benchmark_report(institution_id):
    conn = connect_to_db(
        host=environ.get("DB_HOST"),
        port=int(environ.get("DB_PORT")),
        user=environ.get("DB_USER"),
        password=environ.get("DB_PASSWORD"),
        db_name=environ.get("DB_NAME"),
    )
    query = """
        SELECT 
            U.name AS Usuario, 
            COUNT(UP.stepId) AS Etapas_Completadas
        FROM Users U
        JOIN Enrollments E ON U.id = E.userId
        LEFT JOIN UserProgress UP ON E.id = UP.enrollmentId
        WHERE E.isActive = 1  -- Apenas inscrições ativas
        AND E.courseId IN (
            SELECT id FROM Courses WHERE institutionId = 3  -- Filtra por instituição
        )
        GROUP BY U.id, U.name
    """
    df_benchmark = pd.read_sql(query, conn, params=[institution_id])

    plt.figure(figsize=(10, 6))
    sns.barplot(x="Usuario", y="Etapas_Completadas", data=df_benchmark, palette="viridis")

    plt.title("Desempenho dos Usuários - Etapas Completadas", fontsize=14)
    plt.xlabel("Usuário", fontsize=12)
    plt.ylabel("Total de Etapas Completadas", fontsize=12)
    plt.xticks(rotation=45, ha="right")
    plt.grid(True, axis="y", linestyle="--")

    plt.tight_layout()
    bio = BytesIO()
    plt.savefig(bio, format="png")
    bio.seek(0)
    return base64.b64encode(bio.read())


def user_gender_distribution(institution_id):
    conn = connect_to_db(
        host=environ.get("DB_HOST"),
        port=int(environ.get("DB_PORT")),
        user=environ.get("DB_USER"),
        password=environ.get("DB_PASSWORD"),
        db_name=environ.get("DB_NAME"),
    )
    query_gender = """
    SELECT U.gender, COUNT(*) AS Total_Usuarios
    FROM Users U
    JOIN Enrollments E ON U.id = E.userId
    JOIN Courses C ON E.courseId = C.id
    WHERE C.institutionId = %s  -- Filtra apenas os usuários da instituição específica
    GROUP BY U.gender
    """
    df_gender = pd.read_sql(query_gender, conn, params=[institution_id])

    plt.figure(figsize=(8, 6))
    sns.barplot(x="gender", y="Total_Usuarios", data=df_gender, palette="coolwarm")
    plt.title("Distribuição de Gênero dos Usuários")
    plt.xlabel("Gênero")
    plt.ylabel("Total de Usuários")
    bio = BytesIO()
    plt.savefig(bio, format="png")
    bio.seek(0)
    return base64.b64encode(bio.read())


def user_activity_over_week(institution_id):
    conn = connect_to_db(
        host=environ.get("DB_HOST"),
        port=int(environ.get("DB_PORT")),
        user=environ.get("DB_USER"),
        password=environ.get("DB_PASSWORD"),
        db_name=environ.get("DB_NAME"),
    )
    query_weekday_activity_per_user = """
    SELECT 
        U.name AS Usuario,
        CASE 
            WHEN DAYOFWEEK(UP.progressDate) = 1 THEN 'Domingo'
            WHEN DAYOFWEEK(UP.progressDate) = 2 THEN 'Segunda-feira'
            WHEN DAYOFWEEK(UP.progressDate) = 3 THEN 'Terça-feira'
            WHEN DAYOFWEEK(UP.progressDate) = 4 THEN 'Quarta-feira'
            WHEN DAYOFWEEK(UP.progressDate) = 5 THEN 'Quinta-feira'
            WHEN DAYOFWEEK(UP.progressDate) = 6 THEN 'Sexta-feira'
            WHEN DAYOFWEEK(UP.progressDate) = 7 THEN 'Sábado'
        END AS Dia_Semana,
        COUNT(*) AS Total_Atividades
    FROM UserProgress UP
    JOIN Enrollments E ON UP.enrollmentId = E.id
    JOIN Users U ON E.userId = U.id
    JOIN Courses C ON E.courseId = C.id
    WHERE C.institutionId = %s
    GROUP BY Usuario, Dia_Semana
    ORDER BY Usuario, FIELD(Dia_Semana, 'Segunda-feira', 'Terça-feira', 'Quarta-feira', 'Quinta-feira', 'Sexta-feira', 'Sábado', 'Domingo')
    """
    df_weekday_user = pd.read_sql(query_weekday_activity_per_user, conn, params=[institution_id])

    plt.figure(figsize=(12, 6))
    sns.lineplot(x="Dia_Semana", y="Total_Atividades", hue="Usuario", data=df_weekday_user, marker="o")
    plt.title("Atividade de Usuários por Dia da Semana")
    plt.xlabel("Dia da Semana")
    plt.ylabel("Total de Atividades")
    plt.xticks(rotation=45)
    plt.grid(axis="y", linestyle="--", alpha=0.7)

    plt.legend(title="Usuário", bbox_to_anchor=(1.05, 1), loc="upper left")

    bio = BytesIO()
    plt.savefig(bio, format="png")
    bio.seek(0)
    return base64.b64encode(bio.read())


def course_completion_report(institution_id):
    conn = connect_to_db(
        host=environ.get("DB_HOST"),
        port=int(environ.get("DB_PORT")),
        user=environ.get("DB_USER"),
        password=environ.get("DB_PASSWORD"),
        db_name=environ.get("DB_NAME"),
    )
    query_course_completion = """
    SELECT i.name AS Instituicao, c.name AS Curso, COUNT(e.id) AS Total_Inscritos, 
        COUNT(DISTINCT up.enrollmentId) AS Total_Concluidos
    FROM Enrollments e
    JOIN Courses c ON e.courseId = c.id
    JOIN Institutions i ON c.institutionId = i.id
    LEFT JOIN UserProgress up ON e.id = up.enrollmentId
    WHERE i.id = %s
    GROUP BY i.name, c.name
    """
    df_completion = pd.read_sql(query_course_completion, conn, params=[institution_id])
    df_completion["Taxa_Conclusao"] = (df_completion["Total_Concluidos"] / df_completion["Total_Inscritos"]) * 100

    plt.figure(figsize=(12, 8))
    sns.barplot(x="Taxa_Conclusao", y="Instituicao", hue="Curso", data=df_completion, palette="muted")
    plt.title("Taxa de Conclusão de Cursos por Instituição")
    plt.xlabel("Taxa de Conclusão (%)")
    plt.ylabel("Instituição")

    # Posicionar a legenda fora do gráfico
    plt.legend(title="Curso", bbox_to_anchor=(1.05, 1), loc="upper left")
    plt.tight_layout()
    bio = BytesIO()
    plt.savefig(bio, format="png")
    bio.seek(0)
    return base64.b64encode(bio.read())


def favorited_courses(institution_id):
    conn = connect_to_db(
        host=environ.get("DB_HOST"),
        port=int(environ.get("DB_PORT")),
        user=environ.get("DB_USER"),
        password=environ.get("DB_PASSWORD"),
        db_name=environ.get("DB_NAME"),
    )
    query_favorites = """
    SELECT c.name AS Curso, COUNT(fc.userId) AS Total_Favoritos
    FROM FavoritedCourses fc
    JOIN Courses c ON fc.courseId = c.id
    WHERE c.institutionId = %s
    GROUP BY c.id, c.name
    ORDER BY Total_Favoritos ASC 
    """
    df_favorites = pd.read_sql(query_favorites, conn, params=[institution_id])

    df_favorites = df_favorites.sort_values(by="Total_Favoritos", ascending=True)

    plt.figure(figsize=(10, 6))
    sns.barplot(x="Total_Favoritos", y="Curso", data=df_favorites, palette="coolwarm")
    plt.title("Cursos Mais Favoritados da Instituição (Ordem Crescente)")
    plt.xlabel("Total de Favoritos")
    plt.ylabel("Curso")
    plt.grid(axis="x", linestyle="--", alpha=0.7)

    bio = BytesIO()
    plt.savefig(bio, format="png")
    bio.seek(0)
    return base64.b64encode(bio.read())


def incomplete_steps_analysis(institution_id):
    conn = connect_to_db(
        host=environ.get("DB_HOST"),
        port=int(environ.get("DB_PORT")),
        user=environ.get("DB_USER"),
        password=environ.get("DB_PASSWORD"),
        db_name=environ.get("DB_NAME"),
    )
    query_incomplete_steps = """
    SELECT s.title AS Etapa, c.name AS Curso, 
        (COUNT(e.id) - COUNT(DISTINCT up.enrollmentId)) AS Total_Nao_Completas
    FROM Steps s
    JOIN Courses c ON s.courseId = c.id
    LEFT JOIN UserProgress up ON s.id = up.stepId
    LEFT JOIN Enrollments e ON e.courseId = s.courseId
    WHERE c.institutionId = %s
    GROUP BY s.id, s.title, c.id, c.name
    """
    df_incomplete_steps = pd.read_sql(query_incomplete_steps, conn, params=[institution_id])

    plt.figure(figsize=(12, 8))
    sns.barplot(x="Total_Nao_Completas", y="Etapa", hue="Curso", data=df_incomplete_steps, palette="magma")
    plt.title("Etapas Não Completadas por Curso")
    plt.xlabel("Total de Não Completadas")
    plt.ylabel("Etapa")
    plt.legend(title="Curso", bbox_to_anchor=(1.05, 1), loc="upper left")
    plt.grid(axis="x", linestyle="--", alpha=0.7)
    plt.tight_layout()
    bio = BytesIO()
    plt.savefig(bio, format="png")
    bio.seek(0)
    return base64.b64encode(bio.read())


def activity_performance(institution_id):
    conn = connect_to_db(
        host=environ.get("DB_HOST"),
        port=int(environ.get("DB_PORT")),
        user=environ.get("DB_USER"),
        password=environ.get("DB_PASSWORD"),
        db_name=environ.get("DB_NAME"),
    )
    query_activity_performance = """
    SELECT c.name AS Curso, 
        a.allowedAttempts AS Tentativas_Permitidas, 
        AVG(at.score) AS Media_Pontuacao, 
        COUNT(at.id) AS Total_Tentativas
    FROM Activities a
    JOIN Steps s ON a.stepId = s.id
    JOIN Courses c ON s.courseId = c.id
    LEFT JOIN ActivityAttempts at ON a.id = at.activityId
    WHERE c.institutionId = %s
    GROUP BY c.id, c.name, a.allowedAttempts
    """

    df_activity_perf = pd.read_sql(query_activity_performance, conn, params=[institution_id])

    plt.figure(figsize=(10, 6))
    sns.barplot(x="Media_Pontuacao", y="Curso", hue="Tentativas_Permitidas", data=df_activity_perf, palette="coolwarm")
    plt.title("Desempenho em Atividades Avaliativas")
    plt.xlabel("Pontuação Média")
    plt.ylabel("Curso")
    plt.xticks(rotation=45, ha="right")
    plt.legend(title="Tentativas Permitidas", bbox_to_anchor=(1.05, 1), loc="upper left")
    plt.grid(axis="x", linestyle="--", alpha=0.7)
    plt.tight_layout()
    bio = BytesIO()
    plt.savefig(bio, format="png")
    bio.seek(0)
    return base64.b64encode(bio.read())


def completed_steps_within_time_rate(institution_id):
    conn = connect_to_db(
        host=environ.get("DB_HOST"),
        port=int(environ.get("DB_PORT")),
        user=environ.get("DB_USER"),
        password=environ.get("DB_PASSWORD"),
        db_name=environ.get("DB_NAME"),
    )
    query_on_time = """
    SELECT c.name AS Curso, 
        COUNT(CASE WHEN up.progressDate <= DATE_ADD(e.enrollmentDate, INTERVAL IFNULL(c.requiredTimeLimit, 0) DAY) THEN 1 END) AS Dentro_Prazo,
        COUNT(up.stepId) AS Total_Atividades
    FROM Courses c
    LEFT JOIN Enrollments e ON e.courseId = c.id
    LEFT JOIN UserProgress up ON e.id = up.enrollmentId
    WHERE c.institutionId = %s
    GROUP BY c.id, c.name
    ORDER BY Dentro_Prazo DESC
    """

    df_on_time = pd.read_sql(query_on_time, conn, params=[institution_id])

    df_on_time["Taxa_Dentro_Prazo"] = (
        df_on_time["Dentro_Prazo"] / df_on_time["Total_Atividades"].replace(0, np.nan)
    ) * 100
    df_on_time.fillna(0, inplace=True)

    plt.figure(figsize=(10, 6))
    sns.barplot(x="Taxa_Dentro_Prazo", y="Curso", data=df_on_time, palette="mako")

    plt.title("Taxa de Atividades Concluídas Dentro do Prazo")
    plt.xlabel("Taxa de Conclusão Dentro do Prazo (%)")
    plt.ylabel("Curso")
    plt.xlim(0, 100)
    plt.grid(axis="x", linestyle="--", alpha=0.7)

    bio = BytesIO()
    plt.savefig(bio, format="png")
    bio.seek(0)
    return base64.b64encode(bio.read())
