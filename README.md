# ATLoad
A Python library for benchmark workload generators. It enables the generation of
reproducible bursty workloads that are representative of online services.

* ATLoad uses a closed-loop: a client can only send a new request after its
previous request has returned.
* ATLoad generates think times (i.e., time intervals between consecutive
client requests) using a configurable statistical distribution (e.g., Poisson,
uniform, or constant).
* ATLoad can inject burstiness to the generation of think times using a
*Markovian Arrival Process (MAP)*, as described in this
[paper](https://dl.acm.org/doi/abs/10.1145/1555228.1555267).
* ATLoad generates a request mix using a graph where nodes represent request
types and arc weights represent probabilities of transitioning between request
types.

## Workload Configuration
This configuration specifies a bursty workload that simulates 200 clients
sending 3 types of requests (`write`, `read`, and `delete`) for 300 seconds. The
mean think time is 10 seconds (5 seconds during a burst).
```
sessions: 200                     # number of concurrent sessions
duration:
  total: 300                      # total duration in seconds
  ramp_up: 60                     # ramp up time in seconds
  ramp_down: 60                   # ramp down time in seconds
think_time: 10                    # mean think time
think_time_distribution: poisson  # distribution of think time (e.g., poisson,
                                  # constant)
burstiness:
  think_time: 5                   # mean bursty think time
  turn_on_prob: 0.2               # probability of turning bursty mode on
  turn_off_prob: 0.1              # probability of turning bursty mode off
request_graph:
  main:
    write: 1.0                    # probability of writing first
    read: 0                       # probability of reading first
    delete: 0                     # probability of deleting first
  write:
    read: .5                      # probability of reading after writing
    delete: .5                    # probability of deleting after writing
  read:
    read: .1                      # probability of reading after reading
    delete: .9                    # probability of deleting after reading
  delete:
    read: .3                      # probability of reading after deleting
    delete: .7                    # probability of deleting after deleting
```

## Session Implementation (Python 3)
Requests are made by multiple *sessions* simulating clients. Each session is an
instance of a class that inherits from `ATLoad.Session` and runs on its own
thread. Each request type is implemented by a method of the same name in that
class.

As an example, consider this class that implements a session with those 3
request types (`write`, `read`, and `delete`):
```
import argparse
import datetime

import ATLoad


class Session(ATLoad.Session):
  def write(self):
    # Implement write.
    pass

  def read(self):
    # Implement read.
    pass

  def delete(self):
    # Implement delete.
    pass


if __name__ == "__main__":
  # Parse command-line arguments.
  parser = argparse.ArgumentParser(description="Generate a workload")
  parser.add_argument("--workload_conf", required=True, action="store",
      type=str, help="Path to the workload configuration file")
  parser.add_argument("--log", required=True, action="store", type=str,
      help="Path to the log file")
  parser.add_argument("--seed", required=True, action="store", type=str,
      help="Random number generator seed")
  args = parser.parse_args()
  # Generate workload.
  workload = ATLoad.Workload(args.workload_conf, args.log, Session,
      int(args.seed))
  workload.run()
```

## Developer
- Rodrigo Alves Lima (ral@gatech.edu)

## License
Copyright (C) 2020 Georgia Tech Center for Experimental Research in Computer
Systems.
Licensed under the Apache License 2.0.
