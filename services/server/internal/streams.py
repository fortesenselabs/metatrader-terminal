from models.events import Events


class Streams:
    DataFrame = {
        "name": "Stream:DataFrame",
        "subjects": [Events.DataFrame],
        "max_msgs": 400,
    }
