# init_db.py
import sqlite3, json, os

# Rutas
BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, 'data')
JSON_PATH = os.path.join(DATA_DIR, 'data_clasified.json')
DB_PATH = os.path.join(DATA_DIR, 'tickets.db')

# Esquema SQL
SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS clients (
    id INTEGER PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS incident_types (
    id INTEGER PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS employees (
    id INTEGER PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS tickets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id          INTEGER NOT NULL,
    fecha_apertura     TEXT    NOT NULL,
    fecha_cierre       TEXT    NOT NULL,
    es_mantenimiento   INTEGER NOT NULL,
    satisfaccion       INTEGER NOT NULL,
    incident_type_id   INTEGER NOT NULL,
    es_critico         INTEGER NOT NULL,
    FOREIGN KEY(client_id)        REFERENCES clients(id),
    FOREIGN KEY(incident_type_id) REFERENCES incident_types(id)
);

CREATE TABLE IF NOT EXISTS contacts (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_id   INTEGER NOT NULL,
    employee_id INTEGER NOT NULL,
    fecha       TEXT    NOT NULL,
    tiempo      REAL    NOT NULL,
    FOREIGN KEY(ticket_id)   REFERENCES tickets(id),
    FOREIGN KEY(employee_id) REFERENCES employees(id)
);
"""


def main():
    # 1) Arranca y crea tablas
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.executescript(SCHEMA)

    # 2) Lee JSON
    with open(JSON_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)['tickets_emitidos']

    # 3) Inserta únicos en clients, incident_types y employees
    clients = set()
    types = set()
    emps = set()
    for t in data:
        clients.add(int(t['cliente']))
        types.add(int(t['tipo_incidencia']))
        for c in t['contactos_con_empleados']:
            emps.add(int(c['id_emp']))

    cur.executemany("INSERT INTO clients(id) VALUES(?)", [(c,) for c in clients])
    cur.executemany("INSERT INTO incident_types(id) VALUES(?)", [(i,) for i in types])
    cur.executemany("INSERT INTO employees(id) VALUES(?)", [(e,) for e in emps])

    # 4) Inserta tickets y contactos
    for t in data:
        cur.execute(
            """INSERT INTO tickets
               (client_id, fecha_apertura, fecha_cierre,
                es_mantenimiento, satisfaccion,
                incident_type_id, es_critico)
             VALUES (?,?,?,?,?,?,?)""",
            (
                int(t['cliente']),
                t['fecha_apertura'],
                t['fecha_cierre'],
                1 if t['es_mantenimiento'] else 0,
                int(t['satisfaccion_cliente']),
                int(t['tipo_incidencia']),
                1 if t['es_critico'] else 0
            )
        )
        ticket_id = cur.lastrowid
        for c in t['contactos_con_empleados']:
            cur.execute(
                """INSERT INTO contacts
                   (ticket_id, employee_id, fecha, tiempo)
                 VALUES (?,?,?,?)""",
                (
                    ticket_id,
                    int(c['id_emp']),
                    c['fecha'],
                    float(c['tiempo'])
                )
            )
    conn.commit()
    conn.close()
    print(f"Base de datos creada en {DB_PATH}")


if __name__ == '__main__':
    main()
