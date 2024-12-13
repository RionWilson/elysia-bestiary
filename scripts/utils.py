
from contextlib import contextmanager
from datetime import datetime
from sqlalchemy import and_
from werkzeug.utils import secure_filename

from scripts.models import Creature, Group, session

tables = {

    "Creature": Creature,
    "Group": Group,
}

# db context manager
@contextmanager
def get_session():

    db = session()
    try:
        yield db
    finally:
        db.close()

# fetch group contents
def browse(path):

    results = {"id": path, "creatures": [], "groups": []}

    with get_session() as db:

        # get full path
        results["path"] = get_full_path(db, path)

        # parse groups
        query = db.query(Group).filter(Group.path == path).order_by(Group.name.asc(), Group.id.asc())
        for group in query:
            results["groups"].append(
            {
                "type": "group",
                "id": group.id,
                "name": group.name,
            })

        # parse creatures
        query = db.query(Creature).filter(Creature.path == path).order_by(Creature.name.asc(), Creature.id.asc())
        for creature in query:
            results["creatures"].append(
            {
                "type": "creature",
                "id": creature.id,
                "name": creature.name,
                "created": creature.created.strftime("%-m/%-d/%Y"),
                "modified": creature.modified.strftime("%-m/%-d/%Y"),
                "image": creature.image,
                "stats": creature.stats,
                "text": creature.text,
            })
    
    return results

def get_full_path(db, path):

    # catch special cases
    if path == "search":
        return [{"id": "search", "name": "Search Results"}]
    elif path == "trash":
        return [{"id": "trash", "name": "Recycle Bin"}]

    file_tree = []

    # recursive indexing
    while path is not None:
        query = db.query(Group).get(path)
        file_tree.insert(0,
        {
            "id": path, "name": query.name,
        })
        path = query.path

    # append home directory
    file_tree.insert(0, {"id": None, "name": "Home"})

    return file_tree

def elevate_path(path):

    # query parent
    with get_session() as db:
        return browse(db.query(Group).get(path).path)

def get_creature(path):

    # query entry
    with get_session() as db:
        entry = db.query(Creature).get(path)
        return {
            "id": path,
            "image": entry.image,
            "name": entry.name,
            "stats": entry.stats,
            "text": entry.text,
        }

def update_entry(table, path, config):

    # parse config
    with get_session() as db:
        entry = db.query(tables[table]).get(path)
        for key in config.keys():
            setattr(entry, key, config[key])
        db.commit()

def update_image(path, extension):
    
    # verify file
    sanitized = secure_filename(f"{path}.{extension}")
    update_entry("Creature", path, {

        "image": f"/static/upload/{sanitized}",
    })


def create_entry(table, config):

    # parse config
    with get_session() as db:
        entry = tables[table](**config)
        db.add(entry)
        db.commit()

        print(f"Created: {entry.id} [{table}]!")

def destroy_entry(table, path):

    # filter by id
    with get_session() as db:
        entry = db.query(tables[table]).get(path)
        db.delete(entry)
        db.commit()

    print(f"Destroyed: {path} [{table}]!")
