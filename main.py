import bryan
from yak_parser.StatechartParser import StatechartParser


statechart = StatechartParser().parse(path='02_light_switch2.ysc')

statechart.save_hierarchy_image('02_light_switch2.svg')
statechart.print_transitions()


bryan.process(statechart)


statechart.save_hierarchy_image('02_light_switch2_processed.svg')
statechart.print_transitions()
