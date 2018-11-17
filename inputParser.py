import pendulum
import re

_FUZZY_DAYS = ['yesterday', 'tonight', 'today', 'tomorrow',
               'sun', 'mon', 'tue', 'wed', 'thu', 'fri', 'sat']

def _parseDate(string):
        """parse date"""
        date = string[:3].lower()
        if date in _FUZZY_DAYS or string.lower() in _FUZZY_DAYS:
            if date == 'yes':
                date_string = pendulum.yesterday('US/Pacific').format('YYYY-MM-DD')
                #print(date_string)
                return date_string
            elif date == 'tod' or date == 'ton':
                date_string = pendulum.now('US/Pacific').format('YYYY-MM-DD')
                return date_string
            elif date == 'tom':
                date_string = pendulum.tomorrow('US/Pacific').format('YYYY-MM-DD')
                return date_string
            elif date == 'sun':
                date_string = pendulum.now('US/Pacific').next(pendulum.SUNDAY).format('YYYY-MM-DD')
                return date_string
            elif date == 'mon':
                date_string = pendulum.now('US/Pacific').next(pendulum.MONDAY).format('YYYY-MM-DD')
                return date_string
            elif date == 'tue':
                date_string = pendulum.now('US/Pacific').next(pendulum.TUESDAY).format('YYYY-MM-DD')
                return date_string
            elif date == 'wed':
                date_string = pendulum.now('US/Pacific').next(pendulum.WEDNESDAY).format('YYYY-MM-DD')
                return date_string
            elif date == 'thu':
                date_string = pendulum.now('US/Pacific').next(pendulum.THURSDAY).format('YYYY-MM-DD')
                return date_string
            elif date == 'fri':
                date_string = pendulum.now('US/Pacific').next(pendulum.FRIDAY).format('YYYY-MM-DD')
                return date_string
            elif date == 'sat':
                date_string = pendulum.now('US/Pacific').next(pendulum.SATURDAY).format('YYYY-MM-DD')
                return date_string

def parseInput(args=None, _TEAM_BY_TRI=None, _TEAM_BY_NICK=None):
        """parse user input from mlb2"""
        # return team, date, timezone

        tz = 'US/Eastern'
        date = None
        team = None
        is_date = None

        if not args:
            return team, date, tz

        arg_array = []
        for arg in args.split(' '):
            arg_array.append(arg)
        
        for idx, arg in enumerate(arg_array):
            #print(arg)
            if '--tz' in arg:
                #print(arg_array[idx+1])
                try:
                    tz = arg_array[idx+1]
                except:
                    tz = 'US/Eastern'
            if arg.lower() in _FUZZY_DAYS or arg[:3].lower() in _FUZZY_DAYS:
                date = _parseDate(arg)
                #print(date)
                #date = pendulum.parse(date).in_tz(tz)
            try:
                arg = arg.strip('-')
                arg = arg.strip('/')
                if arg[0].isdigit() and arg[1].isdigit() and arg[2].isalpha():
                    if arg[-1].isdigit():
                        yr = arg[-2:]
                        mnth = " ".join(re.findall("[a-zA-Z]+", arg))
                        #print(mnth,yr)
                        rebuild = '{}-{}-{}'.format(mnth, arg[:2], yr)
                    else:
                        rebuild = arg[2:] + arg[:2]
                    #print('both', rebuild)
                elif arg[0].isdigit() and arg[1].isalpha():
                    rebuild = arg[1:] + arg[0]
                    #print('one', rebuild)
                else:
                    rebuild = arg
                    
                #print(rebuild)
                is_date = pendulum.parse(rebuild, strict=False)
                #print(is_date)
            except:
                is_date = None
            if is_date:
                date = is_date.format('YYYY-MM-DD')
            if _TEAM_BY_TRI and _TEAM_BY_NICK:
                if arg.upper() in _TEAM_BY_TRI:
                    team = str(_TEAM_BY_TRI[arg.upper()])
                elif arg.lower() in _TEAM_BY_NICK:
                    abbr = str(_TEAM_BY_NICK[arg.lower()])
                    team = str(_TEAM_BY_TRI[abbr])
                #else:
                #    team = arg.upper()

        return team, date, tz