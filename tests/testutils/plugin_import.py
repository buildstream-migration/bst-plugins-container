import os
import pytest
import shutil

PLUGIN_ROOT = "bst_plugins_container"

@pytest.fixture()
def plugin_import(datafiles):
    project = str(datafiles)
    owndir = os.path.dirname(os.path.realpath(__file__))
    topdir = os.path.realpath(os.path.join(owndir, "..", ".."))
    plugins_dir = os.path.join(project, "plugins")
    elements_src = os.path.join(topdir, PLUGIN_ROOT, "elements")
    elements_dst = os.path.join(plugins_dir, "elements")
    sources_src = os.path.join(topdir, PLUGIN_ROOT, "sources")
    sources_dst = os.path.join(plugins_dir, "sources")

    if os.path.exists(elements_src):
        os.makedirs(elements_dst, exist_ok=True)
        for f in os.listdir(elements_src):
            if f is not "__init__.py" and (f.endswith(".py") or f.endswith(".yaml")):
                fsrc = os.path.join(elements_src, f)
                fdst = os.path.join(elements_dst ,f)
                shutil.copyfile(fsrc, fdst)

    if os.path.exists(sources_src):
        os.makedirs(sources_dst, exist_ok=True)
        for f in os.listdir(sources_src):
            if f is not "__init__.py" and (f.endswith(".py") or f.endswith(".yaml")):
                fsrc = os.path.join(sources_src, f)
                fdst = os.path.join(sources_dst ,f)
                shutil.copyfile(fsrc, fdst)

    yield plugins_dir

    shutil.rmtree(plugins_dir)
