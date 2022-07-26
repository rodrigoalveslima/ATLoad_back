# Copyright (C) 2020 Georgia Tech Center for Experimental Research in Computer
# Systems

import collections
import multiprocessing
import os
import random
import threading
import time

import numpy
import yaml


class Session:
  def _run(self, start_time, start_at, stop_at, request_graph, think_time,
      think_time_distribution):
    self._logs = []
    self._request_graph = request_graph
    # Wait to start.
    while time.time() < start_at:
      time.sleep(0.1)
    # Session loop.
    request = "main"
    while time.time() < stop_at:
      request = self._select_next_request(request)
      getattr(self, request)()
      if think_time_distribution:
        think_time_generator = getattr(numpy.random, think_time_distribution)
        time.sleep(max(0, min(
            think_time_generator(think_time[int(time.time() - start_time)]),
            stop_at - time.time())))
      else:
        time.sleep(min(think_time[int(time.time() - start_time)],
            stop_at - time.time()))

  def _select_next_request(self, request):
    r = random.uniform(0, sum(self._request_graph[request].values()))
    for request, weight in self._request_graph[request].items():
      if r < weight:
        return request
      r -= weight

  def _log(self, message):
    self._logs.append((time.time(), message))


class Workload:
  def __init__(self, conf_filename, log_filename, session_cls, random_seed,
      n_workers, *args):
    # Initialize the random number generator.
    random.seed(random_seed)
    # Parse configuration file and copy parameters.
    with open(conf_filename) as conf_file:
      conf = yaml.safe_load(conf_file)
    self._log_filename = log_filename
    self._session_cls = session_cls
    self._n_workers = n_workers
    self._args = args
    self._n_sessions = conf["sessions"]
    self._duration = conf["duration"]
    self._request_graph = dict([(request, collections.OrderedDict(
        conf["request_graph"][request])) for request in conf["request_graph"]])
    self._think_time_distribution = conf["think_time_distribution"] \
        if conf["think_time_distribution"] != "constant" else None
    # Generate mean think times using a Markovian Arrival Process (MAP) for burstiness.
    self._think_time = []
    burstiness_on = False
    for i in range(int(conf["duration"]["total"]) + 60):
      if "burstiness" in conf:
        if burstiness_on and random.uniform(0, 1) < conf["burstiness"]["turn_off_prob"]:
          burstiness_on = False
        elif not burstiness_on and random.uniform(0, 1) < conf["burstiness"]["turn_on_prob"]:
          burstiness_on = True
      self._think_time.append(conf["burstiness"]["think_time"] if burstiness_on else conf["think_time"])

  def _run_worker(self, log_filename, start_time, n_sessions):
    # Initialize sessions.
    sessions = [self._session_cls(*self._args) for i in range(n_sessions)]
    # Run each session in its own thread.
    threads = [threading.Thread(target=session._run, args=[
        start_time,
        start_time + self._duration["ramp_up"] * (i / n_sessions),
        start_time + self._duration["total"] -
            self._duration["ramp_down"] * (i / n_sessions),
        self._request_graph,
        self._think_time,
        self._think_time_distribution])
        for (i, session) in enumerate(sessions)]
    for thread in threads:
      thread.start()
    # Wait until all sessions are finished.
    for thread in threads:
      thread.join()
    # Arrange session logs in chronological order.
    logs = []
    while True:
      session_i = None
      for (i, session) in enumerate(sessions):
        if session._logs and (session_i is None or
            session._logs[0][0] < sessions[session_i]._logs[0][0]):
          session_i = i
      if session_i is None:
        break
      logs.append(sessions[session_i]._logs.pop(0)[1])
    # Write logs to a file.
    with open(log_filename, 'w') as log_file:
      for (i, log) in enumerate(logs):
        if i:
          log_file.write("\n")
        log_file.write(log)

  def run(self):
    start_time = time.time()
    dirname = os.path.dirname(self._log_filename)
    filename, extension = os.path.basename(self._log_filename).split('.')
    workers = [multiprocessing.Process(target=self._run_worker, args=(
            os.path.join(dirname, filename + str(i) + '.' + extension),
            start_time, int(self._n_sessions // self._n_workers)))
        for i in range(self._n_workers)]
    # Run each worker in its own process.
    for worker in workers:
      worker.start()
    # Wait until all workers are finished.
    for worker in workers:
      worker.join()