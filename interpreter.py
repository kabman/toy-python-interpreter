class Interpreter:
    def __init__(self):
        self.stack=[]
        self.environment={}
    
    def STORE_NAME(self, name):
        val = self.stack.pop()
        self.environment[name]=val
    
    def LOAD_NAME(self,name):
        val = self.environment[name]
        self.stack.append(val)
    
    def parse_argument(self,instruction,argument,what_to_execcute):
        numbers = ["LOAD_VALUE"]
        names = ["LOAD_NAME","STORE_NAME"]

        if instruction in numbers:
            argument = what_to_execute["numbers"][argument]
        elif instruction in names:
            argument = what_to_execute["names"][argument]

        return argument

    def Load_VALUE(self,number):
        self.stack.apppend(number)
    
    def PRINT_ANSWER(self):
        answer = self.stack.pop()
        print(answer)
    
    def ADD_TWO_VALUES(self):
        first_num = self.stack.pop()
        second_num = self.stack.pop()
        total = first_num + second_num
        self.stack.append(total)
    
    def run_code(self,what_to_execute):
        instructions = what_to_execute["instructions"]
    
        for each_step in instructions:
            instruction,argument = each_step
            argument = self.parse_argument(instruction,argument,what_to_execute)
            if instruction == "LOAD_VALUE":
                
                self.LOAD_VALUE(number)
            elif instruction == "ADD_TWO_VALUES":
                self.ADD_TWO_VALUES()
            elif instruction == "PRINT_ANSWER":
                self.PRINT_ANSWER()
            elif instruction = "STORE_NAME""
                self.STORE_NAME(argument)
            elif instruction == "LOAD_NAME":
                self.LOAD_NAME(argument)

    def execute(self, what_to_execute):
        instructions = what_to_execute["instructions"]
        for each_step in instructions:
            instruction, argument = each_step
            argument = self.parse_argument(instruction, argument, what_to_execute)
            bytecode_method = getattr(self, instruction)
        if argument is None:
            bytecode_method()
        else:
            bytecode_method(argument)

class Frame(object):
    def __init__(self, code_obj, global_names, local_names, prev_frame):
        self.code_obj = code_obj
        self.global_names = global_names
        self.local_names = local_names
        self.prev_frame = prev_frame
        self.stack = []
        if prev_frame:
            self.builtin_names = prev_frame.builtin_names
        else:
            self.builtin_names = local_names['__builtins__']
        if hasattr(self.builtin_names, '__dict__'):
            self.builtin_names = self.builtin_names.__dict__
            self.last_instruction = 0
            self.block_stack = []


class VirtualMachineError(Exception):
    pass
class VirtualMachine(object):
    def __init__(self):
        self.frames = [] # The call stack of frames.
        self.frame = None # The current frame.
        self.return_value = None
        self.last_exception = None
    def run_code(self, code, global_names=None, local_names=None):
        """ An entry point to execute code using the virtual machine."""
        frame = self.make_frame(code, global_names=global_names,
        local_names=local_names)
        self.run_frame(frame)

    def make_frame(self, code, callargs={}, global_names=None, local_names=None):
        if global_names is not None and local_names is not None:
            local_names = global_names
        elif self.frames:
            global_names = self.frame.global_names
            local_names = {}
        else:
            global_names = local_names = {
            '__builtins__': __builtins__,
            '__name__': '__main__',
            '__doc__': None,
            '__package__': None,
            }
            local_names.update(callargs)
            frame = Frame(code, global_names, local_names, self.frame)
        return frame
    def push_frame(self, frame):
        self.frames.append(frame)
        self.frame = frame
    
    def pop_frame(self):
        self.frames.pop()
        if self.frames:
            self.frame = self.frames[-1]
        else:
            self.frame = None
    def top(self):
        return self.frame.stack[-1]
    def pop(self):
        return self.frame.stack.pop()
    def push(self, *vals):
        self.frame.stack.extend(vals)
    def popn(self, n):
        """Pop a number of values from the value stack.
        A list of `n` values is returned, the deepest value first.
        """
        if n:
            ret = self.frame.stack[-n:]
            self.frame.stack[-n:] = []
            return ret
        else:
            return []
    
    def parse_byte_and_args(self):
        f = self.frame
        opoffset = f.last_instruction
        byteCode = f.code_obj.co_code[opoffset]
        f.last_instruction += 1
        byte_name = dis.opname[byteCode]
        if byteCode >= dis.HAVE_ARGUMENT:
            # index into the bytecode
            arg = f.code_obj.co_code[f.last_instruction:f.last_instruction+2]
            f.last_instruction += 2 # advance the instruction pointer
            arg_val = arg[0] + (arg[1] * 256)
            if byteCode in dis.hasconst: # Look up a constant
                arg = f.code_obj.co_consts[arg_val]
            elif byteCode in dis.hasname: # Look up a name
                arg = f.code_obj.co_names[arg_val]
            elif byteCode in dis.haslocal: # Look up a local name
                arg = f.code_obj.co_varnames[arg_val]
            elif byteCode in dis.hasjrel: # Calculate a relative jump
                arg = f.last_instruction + arg_val
            else:
                arg = arg_val
                argument = [arg]
        else:
            argument = []
        return byte_name, argument

    def dispatch(self, byte_name, argument):
        why = None
        try:
            bytecode_fn = getattr(self, 'byte_%s' % byte_name, None)
            if bytecode_fn is None:
                if byte_name.startswith('UNARY_'):
                    self.unaryOperator(byte_name[6:])
                elif byte_name.startswith('BINARY_'):
                    self.binaryOperator(byte_name[7:])
                else:
                    raise VirtualMachineError(
                    "unsupported bytecode type: %s" % byte_name
                    )
            else:
                why = bytecode_fn(*argument)
        except:
            # deal with exceptions encountered while executing the op.
            self.last_exception = sys.exc_info()[:2] + (None,)
            why = 'exception'
            return why
    def run_frame(self, frame):
        """Run a frame until it returns (somehow).
        Exceptions are raised, the return value is returned.
        """
        self.push_frame(frame)
        while True:
            byte_name, arguments = self.parse_byte_and_args()
            why = self.dispatch(byte_name, arguments)
            # Deal with any block management we need to do
            while why and frame.block_stack:
                why = self.manage_block_stack(why)
                if why:
                    break
                self.pop_frame()
                if why == 'exception':
                    exc, val, tb = self.last_exception
                    e = exc(val)
                    e.__traceback__ = tb
                    raise e
                return self.return_value
    def byte_LOAD_CONST(self, const):
        self.push(const)
        def byte_POP_TOP(self):
        self.pop()
    def byte_LOAD_NAME(self, name):
        frame = self.frame
        if name in frame.f_locals:
            val = frame.f_locals[name]
        elif name in frame.f_globals:
            val = frame.f_globals[name]
        elif name in frame.f_builtins:
            val = frame.f_builtins[name]
        else:
            raise NameError("name '%s' is not defined" % name)
            self.push(val)
    def byte_STORE_NAME(self, name):
        self.frame.f_locals[name] = self.pop()
    def byte_LOAD_FAST(self, name):
        if name in self.frame.f_locals:
            val = self.frame.f_locals[name]
        else:
            raise UnboundLocalError("local variable '%s' referenced before assignment" % name)
            self.push(val)
    def byte_STORE_FAST(self, name):
        self.frame.f_locals[name] = self.pop()
    def byte_LOAD_GLOBAL(self, name):
        f = self.frame
        if name in f.f_globals:
            val = f.f_globals[name]
        elif name in f.f_builtins:
            val = f.f_builtins[name]
        else:
            raise NameError("global name '%s' is not defined" % name)
        self.push(val)

    BINARY_OPERATORS = {
    'POWER': pow,
    'MULTIPLY': operator.mul,
    'FLOOR_DIVIDE': operator.floordiv,
    'TRUE_DIVIDE': operator.truediv,
    'MODULO': operator.mod,
    'ADD': operator.add,
    'SUBTRACT': operator.sub,
    'SUBSCR': operator.getitem,
    'LSHIFT': operator.lshift,
    'RSHIFT': operator.rshift,
    'AND': operator.and_,
    'XOR': operator.xor,
    'OR': operator.or_,
    }

    def binaryOperator(self, op):
        x, y = self.popn(2)
        self.push(self.BINARY_OPERATORS[op](x, y))
    COMPARE_OPERATORS = [
    operator.lt,
    operator.le,
    operator.eq,
    operator.ne,
    operator.gt,
    operator.ge,
    lambda x, y: x in y,
    lambda x, y: x not in y,
    lambda x, y: x is y,
    lambda x, y: x is not y,
    lambda x, y: issubclass(x, Exception) and issubclass(x, y),
    ]
    def byte_COMPARE_OP(self, opnum):
        x, y = self.popn(2)
        self.push(self.COMPARE_OPERATORS[opnum](x, y))
    ## Attributes and indexing
    def byte_LOAD_ATTR(self, attr):
        obj = self.pop()
        val = getattr(obj, attr)
        self.push(val)
    def byte_STORE_ATTR(self, name):
        val, obj = self.popn(2)
        setattr(obj, name, val)
        ## Building
    def byte_BUILD_LIST(self, count):
        elts = self.popn(count)
        self.push(elts)
    def byte_BUILD_MAP(self, size):
        self.push({})
    def byte_STORE_MAP(self):
        the_map, val, key = self.popn(3)
        the_map[key] = val
        self.push(the_map)
    def byte_LIST_APPEND(self, count):
        val = self.pop()
        the_list = self.frame.stack[-count] # peek
        the_list.append(val)
    ## Jumps
    def byte_JUMP_FORWARD(self, jump):
        self.jump(jump)
    def byte_JUMP_ABSOLUTE(self, jump):
        self.jump(jump)
    def byte_POP_JUMP_IF_TRUE(self, jump):
        val = self.pop()
        if val:
            self.jump(jump)
    def byte_POP_JUMP_IF_FALSE(self, jump):
        val = self.pop()
        if not val:
        self.jump(jump)
## Blocks
    def byte_SETUP_LOOP(self, dest):
        self.push_block('loop', dest)
    def byte_GET_ITER(self):
        self.push(iter(self.pop()))
    def byte_FOR_ITER(self, jump):
        iterobj = self.top()
        try:
            v   = next(iterobj)
            self.push(v)
        except StopIteration:
            self.pop()
            self.jump(jump)
    def byte_BREAK_LOOP(self):
        return 'break'
    def byte_POP_BLOCK(self):
        self.pop_block()

    def byte_MAKE_FUNCTION(self, argc):
        name = self.pop()
        code = self.pop()
        defaults = self.popn(argc)
        globs = self.frame.f_globals
        fn = Function(name, code, globs, defaults, None, self)
        elf.push(fn)
    def byte_CALL_FUNCTION(self, arg):
        lenKw, lenPos = divmod(arg, 256) # KWargs not supported here
        posargs = self.popn(lenPos)
        func = self.pop()
        frame = self.frame
        retval = func(*posargs)
        self.push(retval)
    def byte_RETURN_VALUE(self):
        self.return_value = self.pop()
        return "return"




class Function(object):
    """
    Create a realistic function object, defining the things the interpreter expects.
    """
    __slots__ = [
    'func_code', 'func_name', 'func_defaults', 'func_globals',
    'func_locals', 'func_dict', 'func_closure',
    '__name__', '__dict__', '__doc__',
    '_vm', '_func',
    ]
    def __init__(self, name, code, globs, defaults, closure, vm):
        """You don't need to follow this closely to understand the interpreter."""
        self._vm = vm
        self.func_code = code
        self.func_name = self.__name__ = name or code.co_name
        self.func_defaults = tuple(defaults)
        self.func_globals = globs
        self.func_locals = self._vm.frame.f_locals
        self.__dict__ = {}
        self.func_closure = closure
        self.__doc__ = code.co_consts[0] if code.co_consts else None
        # Sometimes, we need a real Python function. This is for that.
        kw = {
        'argdefs': self.func_defaults,
        }
        if closure:
            kw['closure'] = tuple(make_cell(0) for _ in closure)
            self._func = types.FunctionType(code, globs, **kw)
    def __call__(self, *args, **kwargs):
        callargs = inspect.getcallargs(self._func, *args, **kwargs)
        frame = self._vm.make_frame(self.func_code, callargs, self.func_globals, {})
        return self._vm.run_frame(frame)

def make_cell(value):
    fn = (lambda x: lambda: x)(value)
    return fn.__closure__[0]