import copy

from enum import Enum
from intbase import InterpreterBase


# Enumerated type for our different language data types
class Type(Enum):
    INT = 1
    BOOL = 2
    STRING = 3
    CLOSURE = 4
    NIL = 5
    OBJECT = 6


class Closure:
    def __init__(self, func_ast, env, captured_this=None):
        self.captured_env = self.__selective_deepcopy_env(env)
        self.func_ast = func_ast
        self.type = Type.CLOSURE
        self.captured_this = captured_this
    
    def set_this(self, cur_this):
        self.captured_this = cur_this
        
    def __selective_deepcopy_env(self,env):
        new_env = set()
        
        # print(f"_selective_deepcopy:: {env.__iter__()}")
        env_set = env.__iter__()

        for (var, value) in env_set:
            # print(f"{var} : {value.type()} : {value.value()}")
           
            if var == 'this':
                # print(f"skipping copying this")
                pass
            if value.type() in [Type.CLOSURE, Type.OBJECT]:
                value_to_capture = value
            else:
                value_to_capture = copy.deepcopy(value)
            
            new_env.add((var,value_to_capture))
        return new_env

class Object:
    def __init__(self):
        self.fields={}
        self.methods={}
        self.type = Type.OBJECT
        self.proto = None
    
    def set_field(self,attr_name, value):
        self.fields[attr_name] = value
    
    def get_field(self,attr_name):
        return self.fields.get(attr_name, None)
    
    def set_method(self,attr_name, value):
        self.methods[attr_name] = value
    
    def get_method(self,attr_name):
        return self.methods.get(attr_name, None)
    
    def set_proto(self, parent):
        self.proto = parent
    
    def get_proto(self):
        return Value(Type.OBJECT,self.proto)
    
    def get_attribute(self, name):
        if name in self.fields:
            return self.fields[name]
        elif name in self.methods:
            return self.methods[name]
        else:
            return None

    def print_all_attributes(self):
     
        for field_name, field_value in self.fields.items():
            print(f"         Field {field_name}: {field_value.type()} : {field_value.value()}")

        for method_name, method_value in self.methods.items():
            print(f"         Method {method_name}: {method_value}")

        if self.proto:
            print("         Proto: Set")
            # Optionally, you can recursively print the prototype's details
            self.proto.print_all_attributes()
        else:
            print("         Proto: None")
    



# Represents a value, which has a type and its value
class Value:
    def __init__(self, t, v=None):
        self.t = t
        self.v = v

    def value(self):
        return self.v

    def type(self):
        return self.t

    def set(self, other):
        self.t = other.t
        self.v = other.v

def create_value(val):
    if val == InterpreterBase.TRUE_DEF:
        return Value(Type.BOOL, True)
    elif val == InterpreterBase.FALSE_DEF:
        return Value(Type.BOOL, False)
    elif isinstance(val, int):
        return Value(Type.INT, val)
    elif val == InterpreterBase.NIL_DEF:
        return Value(Type.NIL, None)
    elif isinstance(val, str):
        return Value(Type.STRING, val)


def get_printable(val):
    if val.type() == Type.INT:
        return str(val.value())
    if val.type() == Type.STRING:
        return val.value()
    if val.type() == Type.BOOL:
        if val.value() is True:
            return "true"
        return "false"
    return None
