# Beetimer

Timer for beeminder. For tasks that expect a number of minutes or hours per day.

```
pip install beetimer
beetimer auth <username>
beetimer config time:minutes   # set default time unit (minutes or hours) (default: minutes)
```

# Usage

```
beetimer goals                 # list goals
```

```
beetimer start <goal>
```

```
beetimer stop <goal>
> 38 minutes logged for goal: <goal>. commit 38 points to beeminder? [y/n]
```

or, if hours are the default time unit:

```
beetimer stop <goal>
> 0.63 hours logged for goal: <goal>. commit .63 points to beeminder? [y/n]
```

You can force commit on stop with `--force` or `-f`:

```
beetimer stop <goal> -f
> 38 minutes logged for goal: <goal>. committed 38 points to beeminder.
```
