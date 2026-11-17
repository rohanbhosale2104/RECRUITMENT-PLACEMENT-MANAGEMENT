"""MySQL connectivity helpers: one connection per request, parameterized queries, transactions."""
from contextlib import contextmanager
import mysql.connector
from flask import g
import config


def get_db():
    if 'db' not in g:
        g.db = mysql.connector.connect(**config.DB)
    return g.db


def close_db(exc=None):
    conn = g.pop('db', None)
    if conn is not None:
        conn.close()


def q(sql, args=(), one=False):
    """SELECT helper returning dict rows (always parameterized)."""
    cur = get_db().cursor(dictionary=True)
    cur.execute(sql, args)
    rows = cur.fetchall()
    cur.close()
    return (rows[0] if rows else None) if one else rows


def x(sql, args=()):
    """INSERT/UPDATE helper; returns lastrowid. Call inside tx()."""
    cur = get_db().cursor()
    cur.execute(sql, args)
    last = cur.lastrowid
    cur.close()
    return last


@contextmanager
def tx():
    """START TRANSACTION ... COMMIT, or ROLLBACK if anything fails."""
    conn = get_db()
    if conn.in_transaction:
        conn.rollback()
    conn.start_transaction()
    try:
        yield
        conn.commit()
    except Exception:
        conn.rollback()
        raise
