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
  def _run(self, conf, start_time, start_at, stop_at, request_graph, mean_think_time,
      think_time_generator, intensity):
    self._logs = []
    self._request_graph = request_graph
    # Wait to start.
    while time.time() < start_at:
      time.sleep(0.01)
    # Session loop.
    request = "main"
    while time.time() < stop_at:
      request = self._select_next_request(request)
      request_thread = threading.Thread(target=getattr(self, request), daemon=True)
      request_thread.start()
      think_time = think_time_generator(mean_think_time)
      while think_time > 0:
        time.sleep(0.01)
        think_time -= 0.01 * (intensity if isinstance(intensity, int) else
            intensity[int((time.time() - start_time) / conf["burstiness"]["window"])])
      if conf["loop"] == "closed":
        request_thread.join()

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
      self._conf = yaml.safe_load(conf_file)
    self._log_filename = log_filename
    self._session_cls = session_cls
    self._n_workers = n_workers
    self._args = args
    self._n_sessions = self._conf["sessions"]
    self._duration = self._conf["duration"]
    self._request_graph = dict([(request, collections.OrderedDict(
        self._conf["request_graph"][request])) for request in self._conf["request_graph"]])
    self._mean_think_time = self._conf["think_time"]
    self._think_time_generator = getattr(numpy.random, self._conf["think_time_distribution"]) \
        if self._conf["think_time_distribution"] != "constant" else lambda x: x
    if "burstiness" not in self._conf:
      self._intensity = 1
    else:
      self._intensity = []
      for i in range(int((self._conf["duration"]["total"] + 60) / self._conf["burstiness"]["window"])):
        if i * self._conf["burstiness"]["window"] > self._conf["duration"]["ramp_up"] and \
            i * self._conf["burstiness"]["window"] < self._conf["duration"]["total"] - \
                self._conf["duration"]["ramp_down"]:
          if i == 0 or self._intensity[-1] != 1:
            self._intensity.append(self._conf["burstiness"]["intensity"]
                if random.uniform(0, 1) > self._conf["burstiness"]["turn_off_prob"] else 1)
          else:
            self._intensity.append(self._conf["burstiness"]["intensity"]
                if random.uniform(0, 1) < self._conf["burstiness"]["turn_on_prob"] else 1)
        else:
          self._intensity.append(1)

  def _run_worker(self, log_filename, start_time, n_sessions, start_at_delta):
    # Initialize sessions.
    sessions = [self._session_cls(*self._args) for i in range(n_sessions)]
    # Run each session in its own thread.
    threads = [threading.Thread(target=session._run, args=[
        self._conf,
        start_time,
        start_time + self._duration["ramp_up"] * (i / n_sessions) + start_at_delta,
        start_time + self._duration["total"] -
            self._duration["ramp_down"] * (i / n_sessions),
        self._request_graph,
        self._mean_think_time,
        self._think_time_generator,
        self._intensity])
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
            start_time, int(self._n_sessions // self._n_workers),
            i * self._conf["duration"]["ramp_up"] / self._n_sessions))
        for i in range(self._n_workers)]
    # Run each worker in its own process.
    for worker in workers:
      worker.start()
    # Wait until all workers are finished.
    for worker in workers:
      worker.join()