import json

from notebook.base.handlers import APIHandler
from notebook.utils import url_path_join
import python_pachyderm
import tornado

def get_parents(input):
    if input.pfs.repo != "":
        yield input.pfs.repo
    elif input.cron.name != "":
        yield input.cron.name
    elif input.git.name != "":
        yield input.git.name
    elif len(input.join) > 0:
        for input in input.join:
            yield from get_parents(input)
    elif len(input.cross) > 0:
        for input in input.cross:
            yield from get_parents(input)
    elif len(input.union) > 0:
        for input in input.union:
            yield from get_parents(input)

class DAGHandler(APIHandler):
    # The following decorator should be present on all verb methods (head, get, post, 
    # patch, put, delete, options) to ensure only authorized user can request the 
    # Jupyter server
    @tornado.web.authenticated
    def get(self):
        client = python_pachyderm.Client() # TODO: switch to new_in_cluster
        g = []
        pipeline_names = set()

        for pipeline in client.list_pipeline().pipeline_info:
            pipeline_names.add(pipeline.pipeline.name)

            g.append({
                "id": pipeline.pipeline.name,
                "parentIds": list(get_parents(pipeline.input)),
            })
        for repo in client.list_repo():
            if repo.repo.name not in pipeline_names:
                g.append({
                    "id": repo.repo.name,
                    "parentIds": [],
                })

        self.finish(json.dumps(g))

def setup_handlers(web_app):
    host_pattern = r'.*$'
    base_url = web_app.settings['base_url']
    dag_pattern = url_path_join(base_url, 'pachyderm', 'dag')
    handlers = [(dag_pattern, DAGHandler)]
    web_app.add_handlers(host_pattern, handlers)
