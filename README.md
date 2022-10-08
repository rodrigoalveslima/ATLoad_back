# ATLoad
ATLoad is a Python library for building synthetic workload generators. It
enables the reproducible generation of bursty workloads that are representative
of online services.

* ATLoad clients can be configured to use a closed or open loop for sending
requests. When using a closed loop, a client can only send a new request after
its last request has returned.
* ATLoad clients can be configured to use a specific statistical distribution
(e.g., Poisson, uniform, or constant) for generating think times (i.e., time
intervals between consecutive requests).
* ATLoad clients can be configured to inject burstiness in the workload using a
*Markovian Arrival Process (MAP)*, as described in this
[paper](https://dl.acm.org/doi/abs/10.1145/1555228.1555267).
* ATLoad clients generate a request mix using a configurable graph where nodes
represent request types and arc weights represent probabilities of transitioning
between request types.

## Workload Configuration
This is the configuration for a bursty workload that simulates 200 users sending
3 types of requests (`write`, `read`, and `delete`) for 300 seconds. The mean
think time is 10 seconds.
```
sessions: 200                     # number of concurrent client sessions
loop: closed                      # type of client loop ("closed" or "open")
duration:
  total: 300                      # total duration in seconds
  ramp_up: 60                     # ramp up time in seconds
  ramp_down: 60                   # ramp down time in seconds
think_time: 10                    # mean think time in seconds
think_time_distribution: poisson  # distribution of client think time
                                  # ("poisson", "uniform", or "constant")
burstiness:
  window: 1.0                     # burstiness window in seconds
  intensity: 4                    # burstiness intensity (as a multiplier of
                                  # average workload)
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
Requests are sent by client sessions that simulate real users. Each client
session is an instance of a class inherited from `ATLoad.Session` and runs on
its own thread. Each request type is implemented by a method with the same name
in that class.

This class `Session` is a skeleton for the implementation of those 3 request
types (`write`, `read`, and `delete`):
```
import argparse

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
  parser.add_argument("--n_workers", required=True, action="store", type=str,
      help="Number of worker processes")
  args = parser.parse_args()
  # Generate workload.
  workload = ATLoad.Workload(args.workload_conf, args.log, Session,
      int(args.seed), int(args.n_workers))
  workload.run()
```

## Developer
- Rodrigo Alves Lima (ral@gatech.edu)

## License
Copyright (C) 2022 Georgia Tech Center for Experimental Research in Computer
Systems.

Licensed under the Apache License 2.0.
