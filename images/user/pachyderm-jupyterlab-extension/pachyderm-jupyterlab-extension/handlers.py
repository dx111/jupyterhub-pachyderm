import json

from notebook.base.handlers import APIHandler
from notebook.utils import url_path_join
import tornado

class DAGHandler(APIHandler):
    # The following decorator should be present on all verb methods (head, get, post, 
    # patch, put, delete, options) to ensure only authorized user can request the 
    # Jupyter server
    @tornado.web.authenticated
    def get(self):
        self.finish(json.dumps([
          {
            "id": "0",
            "parentIds": ["8"]
          },
          {
            "id": "1",
            "parentIds": []
          },
          {
            "id": "2",
            "parentIds": []
          },
          {
            "id": "3",
            "parentIds": ["11"]
          },
          {
            "id": "4",
            "parentIds": ["12"]
          },
          {
            "id": "5",
            "parentIds": ["18"]
          },
          {
            "id": "6",
            "parentIds": ["9", "15", "17"]
          },
          {
            "id": "7",
            "parentIds": ["3", "17", "20", "21"]
          },
          {
            "id": "8",
            "parentIds": []
          },
          {
            "id": "9",
            "parentIds": ["4"]
          },
          {
            "id": "10",
            "parentIds": ["16", "21"]
          },
          {
            "id": "11",
            "parentIds": ["2"]
          },
          {
            "id": "12",
            "parentIds": ["21"]
          },
          {
            "id": "13",
            "parentIds": ["4", "12"]
          },
          {
            "id": "14",
            "parentIds": ["1", "8"]
          },
          {
            "id": "15",
            "parentIds": []
          },
          {
            "id": "16",
            "parentIds": ["0"]
          },
          {
            "id": "17",
            "parentIds": ["19"]
          },
          {
            "id": "18",
            "parentIds": ["9"]
          },
          {
            "id": "19",
            "parentIds": []
          },
          {
            "id": "20",
            "parentIds": ["13"]
          },
          {
            "id": "21",
            "parentIds": []
          }
        ]))

def setup_handlers(web_app):
    host_pattern = r'.*$'
    base_url = web_app.settings['base_url']
    dag_pattern = url_path_join(base_url, 'pachyderm', 'dag')
    handlers = [(dag_pattern, DAGHandler)]
    web_app.add_handlers(host_pattern, handlers)
