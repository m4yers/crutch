from cpp import CPPRunner
from runner import Runner


def get_runner(type):
  runners = {'cpp': CPPRunner}
  return runners.get(type, Runner)
