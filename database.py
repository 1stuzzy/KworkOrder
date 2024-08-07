import logging
import datetime
from config import cursor, db


def get_articles(status_filter=None, sort_order='asc'):
    query = "SELECT article_id, status FROM DP_article_edits WHERE status IN ('STARTED', 'DONE', 'ERROR')"
    if status_filter:
        query += " AND status = %s"
    query += " ORDER BY article_id " + ("ASC" if sort_order == 'asc' else "DESC")

    try:
        if status_filter:
            cursor.execute(query, (status_filter,))
        else:
            cursor.execute(query)
        articles = cursor.fetchall()
        return articles
    except Exception as e:
        logging.error(f"Ошибка при выполнении запроса: {e}")
        return []


def get_article_by_id(article_id):
    query = "SELECT article_id, status FROM DP_article_edits WHERE article_id = %s"
    try:
        cursor.execute(query, (article_id,))
        return cursor.fetchone()
    except Exception as e:
        logging.error(f"Ошибка при выполнении запроса: {e}")
        return None


def update_article_status(article_id, user_id, status, time_field=None):
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    if status == 'STARTED':
        query = "UPDATE DP_article_edits SET status = %s, start_time = %s WHERE article_id = %s AND user_id = %s"
        params = (status, now, article_id, user_id)
    elif status == 'DONE':
        query = "UPDATE DP_article_edits SET status = %s, end_time = %s WHERE article_id = %s AND user_id = %s"
        params = (status, now, article_id, user_id)
    else:
        query = "UPDATE DP_article_edits SET status = %s WHERE article_id = %s AND user_id = %s"
        params = (status, article_id, user_id)

    try:
        cursor.execute(query, params)
        db.commit()
    except Exception as e:
        logging.error(f"Ошибка при выполнении запроса: {e}")


def get_user_article_status_history(user_id, limit, offset):
    query = """
    SELECT article_id, status 
    FROM DP_article_status_history 
    WHERE user_id = %s AND status IN ('STARTED', 'DONE')
    ORDER BY article_id
    LIMIT %s OFFSET %s
    """
    try:
        cursor.execute(query, (user_id, limit, offset))
        return cursor.fetchall()
    except Exception as e:
        logging.error(f"Ошибка при выполнении запроса: {e}")
        return []


def count_user_articles(user_id):
    query = "SELECT COUNT(*) FROM DP_article_status_history WHERE user_id = %s AND status IN ('STARTED', 'DONE')"
    try:
        cursor.execute(query, (user_id,))
        return cursor.fetchone()[0]
    except Exception as e:
        logging.error(f"Ошибка при выполнении запроса: {e}")
        return 0



def get_url(article_id):
    query = """
    SELECT 
        DONOR_DOM,
        PROJ_DOM
    FROM TAN_DUB_AL
    WHERE ID_TAB = %s
    """
    try:
        cursor.execute(query, (article_id,))
        result = cursor.fetchone()
        if result:
            return result
        else:
            logging.error(f"Статья с ID {article_id} не найдена.")
            return None
    except Exception as e:
        logging.error(f"Ошибка при выполнении запроса: {e}")
        return None