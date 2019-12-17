# OpenCV Walkthrough

Now that JupyterHub and Pachyderm are running, we'll walk through the canonical [opencv demo](https://github.com/pachyderm/pachyderm/tree/master/examples/opencv), except we'll do everything from JupyterHub.

In JupyterHub:

1) Create a directory called `edges` and add these files to it:

  - A `main.py` with [these contents.](https://github.com/pachyderm/python-pachyderm/blob/master/examples/opencv/edges/main.py) Make sure that it's a python file rather than a notebook.

  - A `requirements.txt` with [these contents.](https://github.com/pachyderm/python-pachyderm/blob/master/examples/opencv/edges/requirements.txt)

Together, these files represent the `edges` pipeline that we'll create from JupyterHub.

2) Run this in a notebook:

```python3

import os
import python_pachyderm

client = python_pachyderm.Client.new_in_cluster()

# Create a repo called images
client.create_repo("images")

# Create a pipeline specifically designed for executing python code. This
# is equivalent to the edges pipeline in the standard opencv example.
python_pachyderm.create_python_pipeline(
    client,
    "./edges",
    python_pachyderm.Input(pfs=python_pachyderm.PFSInput(glob="/*", repo="images")),
)

# Create the montage pipeline
client.create_pipeline(
    "montage",
    transform=python_pachyderm.Transform(cmd=["sh"], image="v4tech/imagemagick", stdin=["montage -shadow -background SkyBlue -geometry 300x300+2+2 $(find /pfs -type f | sort) /pfs/out/montage.png"]),
    input=python_pachyderm.Input(cross=[
        python_pachyderm.Input(pfs=python_pachyderm.PFSInput(glob="/", repo="images")),
        python_pachyderm.Input(pfs=python_pachyderm.PFSInput(glob="/", repo="edges")),
    ])
)


client.put_file_url("images/master", "46Q8nDz.jpg", "http://imgur.com/46Q8nDz.jpg")

with client.commit("images", "master") as commit:
    client.put_file_url(commit, "g2QnNqa.jpg", "http://imgur.com/g2QnNqa.jpg")
    client.put_file_url(commit, "8MN9Kg0.jpg", "http://imgur.com/8MN9Kg0.jpg")
```

This will create the `edges` and `montage` pipelines, and add some images to process.
