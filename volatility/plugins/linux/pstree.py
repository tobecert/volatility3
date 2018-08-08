from volatility.framework.renderers import format_hints
from volatility.framework.objects import utility
from volatility.plugins.linux import pslist

class PsTree(pslist.PsList):
    """Plugin for listing processes in a tree based on their parent process ID """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._processes = {}
        self._levels = {}
        self._children = {}

    def find_level(self, pid):
        """Finds how deep the pid is in the processes list"""
        seen = set([])
        seen.add(pid)
        level = 0
        proc = self._processes.get(pid, None)
        while proc is not None and proc.parent != 0 and proc.parent.pid not in seen:
            ppid = int(proc.parent.pid)

            child_list = self._children.get(ppid, set([]))
            child_list.add(proc.pid)
            self._children[ppid] = child_list
            proc = self._processes.get(ppid, None)
            level += 1
        self._levels[pid] = level

    def _generator(self):
        """Generates the """
        for proc in self.list_tasks(self.context, self.config['primary'], self.config['vmlinux']):
            self._processes[proc.pid] = proc

        # Build the child/level maps
        for pid in self._processes:
            self.find_level(pid)

        def yield_processes(pid):
            proc = self._processes[pid]
            row = (proc.pid,
                   proc.parent.pid,
                   utility.array_to_string(proc.comm))

            yield (self._levels[pid] - 1, row)
            for child_pid in self._children.get(pid, []):
                yield from yield_processes(child_pid)

        for pid in self._levels:
            if self._levels[pid] == 1:
                yield from yield_processes(pid)
