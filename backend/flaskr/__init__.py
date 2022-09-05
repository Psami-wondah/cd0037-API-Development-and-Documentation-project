import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    setup_db(app)

    """
    @TODO: Set up CORS. Allow '*' for origins. Delete the
     sample route after completing the TODOs
    """
    cors = CORS(app, resources={r"/api/*": {"origins": "*"}})

    """
    @TODO: Use the after_request decorator to set Access-Control-Allow
    """

    @app.after_request
    def after_request(response):
        response.headers.add(
            "Access-Control-Allow-Headers", "Content-Type, Authorization"
        )
        response.headers.add(
            "Access-Control-Allow-Headers", "GET, POST, PATCH, DELETE, OPTIONS"
        )
        return response

    """
    @TODO:
    Create an endpoint to handle GET requests
    for all available categories.
    """

    def paginate(request, query_set):
        page = request.args.get("page", 1, type=int)
        page_size = request.args.get("page_size", 10, type=int)
        start = (page - 1) * page_size
        end = start + page_size

        formatted_questions = [question.format() for question in query_set]

        return formatted_questions[start:end]

    @app.route("/categories", methods=["GET"])
    def retrieve_categories():
        categories = Category.query.order_by("id").all()
        categories_dict = {cat.id: cat.type for cat in categories}

        return (
            jsonify(
                {
                    "success": True,
                    "categories": categories_dict,
                    "total_categories": len(categories),
                }
            ),
            200,
        )

    """
    @TODO:
    Create an endpoint to handle GET requests for questions,
    including pagination (every 10 questions).
    This endpoint should return a list of questions,
    number of total questions, current category, categories.

    TEST: At this point, when you start the application
    you should see questions and categories generated,
    ten questions per page and pagination at the bottom of the
     screen for three pages.
    Clicking on the page numbers should update the questions.
    """

    @app.route("/questions", methods=["GET"])
    def questions_route():
        questions = Question.query.order_by("id").all()
        paginated_questions = paginate(request, questions)
        if len(paginated_questions) < 1:
            abort(404)
        categories = Category.query.order_by("id").all()
        categories_dict = {cat.id: cat.type for cat in categories}
        return (
            jsonify(
                {
                    "success": True,
                    "questions": paginated_questions,
                    "total_questions": len(questions),
                    "categories": categories_dict,
                }
            ),
            200,
        )

    """
    @TODO:
    Create an endpoint to DELETE question using a question ID.

    TEST: When you click the trash icon next to a question, the question
     will be removed.
    This removal will persist in the database and when you refresh the page.
    """

    @app.route("/questions/<int:question_id>", methods=["DELETE"])
    def question_route(question_id):
        question = Question.query.filter(
            Question.id == question_id).one_or_none()
        if question:
            question.delete()
            return jsonify({"deleted": question_id, "success": True}), 200
        else:
            abort(404)

    """
    @TODO:
    Create an endpoint to POST a new question,
    which will require the question and answer text,
    category, and difficulty score.

    TEST: When you submit a question on the "Add" tab,
    the form will clear and the question will
    appear at the end of the last page
    of the questions list in the "List" tab.
    """

    @app.route("/questions", methods=["POST"])
    def create_question():
        body = request.get_json()
        question = body.get("question")
        answer = body.get("answer")
        difficulty = body.get("difficulty")
        category = body.get("category")
        searchTerm = body.get("searchTerm", None)

        if searchTerm:
            body = request.get_json()

            questions = (
                Question.query.filter(
                    Question.question.ilike(f"%{searchTerm}%"))
                .order_by("id")
                .all())
            formatted_questions = [question.format() for question in questions]

            return (
                jsonify(
                    {
                        "success": True,
                        "questions": formatted_questions,
                        "total_questions": len(formatted_questions),
                    }
                ),
                200,
            )
        else:

            try:
                question_obj = Question(
                    question=question,
                    answer=answer,
                    difficulty=difficulty,
                    category=category,
                )
                question_obj.insert()
                return jsonify(
                    {"success": True, "created": question_obj.id}), 201
            except Exception as e:
                abort(422)

    """
    @TODO:
    Create a POST endpoint to get questions based on a search term.
    It should return any questions for whom the search term
    is a substring of the question.


    TEST: Search by any phrase. The questions list will update to include
    only question that include that string within their question.
    Try using the word "title" to start.
    """

    """
    @TODO:
    Create a GET endpoint to get questions based on category.

    TEST: In the "List" tab / main screen, clicking on one of the
    categories in the left column will cause only questions of that
    category to be shown.
    """

    @app.route("/categories/<int:category_id>/questions", methods=["GET"])
    def retieve_category_questions(category_id):
        current_category = Category.query.filter(
            Category.id == category_id
        ).one_or_none()

        if current_category:

            questions = (
                Question.query.filter(Question.category == current_category.id)
                .order_by("id")
                .all()
            )
            formatted_questions = [question.format() for question in questions]

            return (
                jsonify(
                    {
                        "success": True,
                        "questions": formatted_questions,
                        "total_questions": len(formatted_questions),
                        "current_category": current_category.type,
                    }
                ),
                200,
            )
        else:
            abort(404)

    """
    @TODO:
    Create a POST endpoint to get questions to play the quiz.
    This endpoint should take category and previous question parameters
    and return a random questions within the given category,
    if provided, and that is not one of the previous questions.

    TEST: In the "Play" tab, after a user selects "All" or a category,
    one question at a time is displayed, the user is allowed to answer
    and shown whether they were correct or not.
    """

    @app.route("/quizzes", methods=["POST"])
    def get_quizzes():
        body = request.get_json()
        previous_questions = body.get("previous_questions", None)
        quiz_category = body.get("quiz_category", None)

        if quiz_category["id"] != 0:
            questions = Question.query.filter(
                Question.category == int(quiz_category["id"])).all()
        else:
            questions = Question.query.all()

        if len(questions) > 0:
            formatted_questions = [question.format() for question in questions]
            formatted_questions = list(
                filter(lambda item: item["id"] not in previous_questions,
                       formatted_questions))

            if len(formatted_questions) > 0:

                index = random.randint(0, len(formatted_questions) - 1)
                question = formatted_questions[index]

                return (
                    jsonify(
                        {
                            "success": True,
                            "question": question,
                        }
                    ),
                    200,
                )
            else:
                return (
                    jsonify(
                        {
                            "success": True
                        }
                    ), 200
                )
        else:
            abort(404)

    """
    @TODO:
    Create error handlers for all expected errors
    including 404 and 422.
    """

    @app.errorhandler(404)
    def not_found(error):
        return (jsonify({"success": False, "error": 404,
                         "message": "resource not found"}), 404, )

    @app.errorhandler(422)
    def unprocessable(error):
        return (
            jsonify({"success": False, "error": 422,
                    "message": "unprocessable"}),
            422,
        )

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({"success": False, "error": 400,
                       "message": "bad request"}), 400

    return app
