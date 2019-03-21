# Write Yourself A Git!
Following this [guide](https://wyag.thb.lt/)

## Description
This is my attempt at understanding `git`'s inner mechanism of
how it stores data and going about implementing some of its porcelain and plumbing commands. I would recommend anyone curious or has the time to try out the tutorial rather than just reading about it.

## Notes
I didn't want to use `argparse` library so I opted
to use `click`. There were some renaming of functions, variables, etc. here and there as it made more sense to me reading it one way vesus another. Objects were written somewhat differently to what I thought was best at the time.

## Considerations/Todos
- [ ] Improve logging :'(
- [ ] Refactor/Less reliance on util level methods
