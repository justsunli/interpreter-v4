import copy
from enum import Enum

from brewparse import parse_program
from env_v4 import EnvironmentManager
from intbase import InterpreterBase, ErrorType
from type_valuev4 import Closure, Object, Type, Value, create_value, get_printable


class ExecStatus(Enum):
    CONTINUE = 1
    RETURN = 2


# Main interpreter class
class Interpreter(InterpreterBase):
    # constants
    NIL_VALUE = create_value(InterpreterBase.NIL_DEF)
    TRUE_VALUE = create_value(InterpreterBase.TRUE_DEF)
    BIN_OPS = {"+", "-", "*", "/", "==", "!=", ">", ">=", "<", "<=", "||", "&&"}

    # methods
    def __init__(self, console_output=True, inp=None, trace_output=False):
        super().__init__(console_output, inp)
        self.trace_output = trace_output
        self.__setup_ops()

    # run a program that's provided in a string
    # uses the provided Parser found in brewparse.py to parse the program
    # into an abstract syntax tree (ast)
    def run(self, program):
        ast = parse_program(program)
        # print("the ast is: ", ast)
        self.__set_up_function_table(ast)
        self.env = EnvironmentManager()
        main_func = self.__get_func_by_name("main", 0)
        if main_func is None:
            super().error(ErrorType.NAME_ERROR, f"Function main not found")
        self.__run_statements(main_func.func_ast.get("statements"))

    def __set_up_function_table(self, ast):
        self.func_name_to_ast = {}
        empty_env = EnvironmentManager()
        for func_def in ast.get("functions"):
            func_name = func_def.get("name")
            num_params = len(func_def.get("args"))
            if func_name not in self.func_name_to_ast:
                self.func_name_to_ast[func_name] = {}
            self.func_name_to_ast[func_name][num_params] = Closure(func_def, empty_env)

    def __get_func_by_name(self, name, num_params):
        # print(f"__get_func_by_name:: for: {name}")
        if name not in self.func_name_to_ast:
            closure_val_obj = self.env.get(name)
            if closure_val_obj is None:
                return None
            if closure_val_obj.type() != Type.CLOSURE:
                super().error(
                    ErrorType.TYPE_ERROR, "Trying to call function with non-closure"
                )
            closure = closure_val_obj.value()
            num_formal_params = len(closure.func_ast.get("args"))
            if num_formal_params != num_params:
                super().error(ErrorType.TYPE_ERROR, "Invalid # of args to lambda")
            return closure_val_obj.value()

        candidate_funcs = self.func_name_to_ast[name]
        if num_params is None:
            # case where we want assign variable to func_name and we don't have
            # a way to specify the # of arguments for the function, so we generate
            # an error if there's more than one function with that name
            if len(candidate_funcs) > 1:
                super().error(
                    ErrorType.NAME_ERROR,
                    f"Function {name} has multiple overloaded versions",
                )
            num_args = next(iter(candidate_funcs))
            closure = candidate_funcs[num_args]
            return closure

        if num_params not in candidate_funcs:
            super().error(
                ErrorType.NAME_ERROR,
                f"Function {name} taking {num_params} params not found",
            )
        return candidate_funcs[num_params]

    def __run_statements(self, statements):
        self.env.push()
        for statement in statements:
            if self.trace_output:
                print("\n")
                print(statement)
            status = ExecStatus.CONTINUE
            if statement.elem_type == InterpreterBase.FCALL_DEF:
                self.__call_func(statement)
            # if its mcall, tell the __call_func method
            if statement.elem_type == InterpreterBase.MCALL_DEF:
                self.__call_func(statement, True)
            elif statement.elem_type == "=":
                self.__assign(statement)
            elif statement.elem_type == InterpreterBase.RETURN_DEF:
                status, return_val = self.__do_return(statement)
            elif statement.elem_type == Interpreter.IF_DEF:
                status, return_val = self.__do_if(statement)
            elif statement.elem_type == Interpreter.WHILE_DEF:
                status, return_val = self.__do_while(statement)
            

            if status == ExecStatus.RETURN:
                self.env.pop()
                return (status, return_val)
        # self.env.print_stack()
        self.env.pop()
        return (ExecStatus.CONTINUE, Interpreter.NIL_VALUE)


    def __call_func(self, call_ast, is_method_call=False):
        func_name = call_ast.get("name")
        
        if func_name == "print":
            return self.__call_print(call_ast)
        if func_name == "inputi":
            return self.__call_input(call_ast)

        actual_args = call_ast.get("args")
        
        # handle method calls
        if is_method_call:
            obj_ref = self.env.get(call_ast.get("objref"))
            if obj_ref.type() != Type.OBJECT:
                super().error(ErrorType.TYPE_ERROR, f"not an object")
            obj_ref_value = obj_ref.value()
            method = self.get_objects_field_or_method(obj_ref_value,func_name)
            if method is None:
                super().error(ErrorType.NAME_ERROR, f"Method {func_name} not found in object {obj_ref}")
            if method.type() != Type.CLOSURE:
                super().error(ErrorType.TYPE_ERROR, f"{func_name} is not a function")
            target_closure = method.value()
            
            
            target_ast = target_closure.func_ast
            
            new_env = {}
            self.__prepare_env_with_closed_variables(target_closure, new_env)
            self.__prepare_params(target_ast,call_ast, new_env)
            self.env.push(new_env)
            
            # set the 'this' 
            self.env.create('this',obj_ref)
            
            _, return_val = self.__run_statements(target_ast.get("statements"))
            self.env.pop()
            
            return return_val
        
        else:
            target_closure = self.__get_func_by_name(func_name, len(actual_args))
            if target_closure == None:
                super().error(ErrorType.NAME_ERROR, f"Function {func_name} not found")
            if target_closure.type != Type.CLOSURE:
                super().error(ErrorType.TYPE_ERROR, f"Function {func_name} is changed to non-function type.")
            target_ast = target_closure.func_ast

            new_env = {}
            current_this = self.env.get('this')
            if current_this is not None:
                target_closure.set_this(current_this)
            self.__prepare_env_with_closed_variables(target_closure, new_env)
            self.__prepare_params(target_ast,call_ast, new_env)
            self.env.push(new_env)
            
            if target_closure.captured_this is not None:
                self.env.set('this',target_closure.captured_this)
            _, return_val = self.__run_statements(target_ast.get("statements"))
            self.env.pop()
   
            return return_val
    
    def get_objects_field_or_method(self,obj,name):
        # check if the method or field exists in the object
        attribute = obj.get_attribute(name)
        if attribute is not None:
            return attribute
        
        # check if there is a proto, call the method recursively if it is
        if obj.proto is not None:
            if name == "proto":
                return obj.get_proto()
            return self.get_objects_field_or_method(obj.proto, name)
        
        return None

    def __prepare_env_with_closed_variables(self, target_closure, temp_env):
        for var_name, value in target_closure.captured_env:
            # Updated here - ignore updates to the scope if we
            #   altered a parameter, or if the argument is a similarly named variable
            temp_env[var_name] = value


    def __prepare_params(self, target_ast, call_ast, temp_env):
        actual_args = call_ast.get("args")
        formal_args = target_ast.get("args")
        if len(actual_args) != len(formal_args):
            super().error(
                ErrorType.NAME_ERROR,
                f"Function {target_ast.get('name')} with {len(actual_args)} args not found",
            )

        for formal_ast, actual_ast in zip(formal_args, actual_args):
            if formal_ast.elem_type == InterpreterBase.REFARG_DEF:
                result = self.__eval_expr(actual_ast)
            else:
                result = copy.deepcopy(self.__eval_expr(actual_ast))
            arg_name = formal_ast.get("name")
            temp_env[arg_name] = result

    def __call_print(self, call_ast):
        output = ""
        # print("__call_print::")
        for arg in call_ast.get("args"):
            # print(f"    the arg elemtype is: {arg.elem_type}")
            value = arg.get("val")
            # print(f"    the arg value is: {value}")
            result = self.__eval_expr(arg)  # result is a Value object
            output = output + get_printable(result)
        super().output(output)
        return Interpreter.NIL_VALUE

    def __call_input(self, call_ast):
        args = call_ast.get("args")
        if args is not None and len(args) == 1:
            result = self.__eval_expr(args[0])
            super().output(get_printable(result))
        elif args is not None and len(args) > 1:
            super().error(
                ErrorType.NAME_ERROR, "No inputi() function that takes > 1 parameter"
            )
        inp = super().get_input()
        if call_ast.get("name") == "inputi":
            return Value(Type.INT, int(inp))
        if call_ast.get("name") == "inputs":
            return Value(Type.STRING, inp)

    def __assign(self, assign_ast):
        
        var_name = assign_ast.get("name")
        rhs_ast = assign_ast.get("expression")
        
        #splitting the variable name on dot to check if its an object field
        if '.' in var_name:
            obj_name, attri = var_name.split('.',1)
            obj = self.env.get(obj_name)
            if obj is None:
                super().error(
                ErrorType.NAME_ERROR, f"{obj_name} doesn't exist"
            )
            if obj.type() != Type.OBJECT:
                super().error(
                ErrorType.TYPE_ERROR, f"{obj_name} is not an object"
            )
            
            # evalute the RHS
            value = self.__eval_expr(rhs_ast)
            obj = obj.value()
            # print(f"        assigning {value.type()} to {attri}")
            if attri == 'proto':
                if value.type() == Type.OBJECT:
                    # print(f"        this is a prototype object")
                    # print(f"        assigning {value.value()} to {attri}")
                    obj.set_proto(value.value())
                elif value.type() == Type.NIL:
                    obj.set_proto(value)
                else:
                    super().error(
                ErrorType.TYPE_ERROR, f"It is not a prototype object"
            )
            else:        
                if value.type() == Type.CLOSURE:
                    obj.set_method(attri,value)
                else:
                    obj.set_field(attri, value)
        
        else:
        
            src_value_obj = copy.copy(self.__eval_expr(assign_ast.get("expression")))
            target_value_obj = self.env.get(var_name)
            if target_value_obj is None:
                self.env.set(var_name, src_value_obj)
            else:
                            # if a close is changed to another type such as int, we cannot make function calls on it any more 
                if target_value_obj.t == Type.CLOSURE and src_value_obj.t != Type.CLOSURE:
                    target_value_obj.v.type = src_value_obj.t
                target_value_obj.set(src_value_obj)

    def __eval_expr(self, expr_ast):
        if expr_ast.elem_type == InterpreterBase.NIL_DEF:
            return Interpreter.NIL_VALUE
        if expr_ast.elem_type == InterpreterBase.INT_DEF:
            return Value(Type.INT, expr_ast.get("val"))
        if expr_ast.elem_type == InterpreterBase.STRING_DEF:
            return Value(Type.STRING, expr_ast.get("val"))
        if expr_ast.elem_type == InterpreterBase.BOOL_DEF:
            return Value(Type.BOOL, expr_ast.get("val"))
        if expr_ast.elem_type == InterpreterBase.VAR_DEF:
            return self.__eval_name(expr_ast)
        if expr_ast.elem_type == InterpreterBase.FCALL_DEF:
            return self.__call_func(expr_ast)
        if expr_ast.elem_type == InterpreterBase.MCALL_DEF:
            return self.__call_func(expr_ast, True)
        if expr_ast.elem_type in Interpreter.BIN_OPS:
            return self.__eval_op(expr_ast)
        if expr_ast.elem_type == Interpreter.NEG_DEF:
            return self.__eval_unary(expr_ast, Type.INT, lambda x: -1 * x)
        if expr_ast.elem_type == Interpreter.NOT_DEF:
            return self.__eval_unary(expr_ast, Type.BOOL, lambda x: not x)
        if expr_ast.elem_type == Interpreter.LAMBDA_DEF:
            return Value(Type.CLOSURE, Closure(expr_ast, self.env))
        if expr_ast.elem_type == Interpreter.OBJ_DEF:
            # print("it is an object def!")
            return Value(Type.OBJECT, Object())

    def __eval_name(self, name_ast):
        
        var_name = name_ast.get("name")
        
        if '.' in var_name:
            obj_name, attr_name = var_name.split('.',1)
            obj = self.env.get(obj_name)

            if obj.type() != Type.OBJECT:
                super().error(
                ErrorType.TYPE_ERROR, f"{obj_name} is not an object"
            )
            
            obj = obj.value()
            
            attribute = self.get_objects_field_or_method(obj,attr_name)
            
            if attribute is not None:
                return attribute
            
            super().error(
                ErrorType.NAME_ERROR, f"attribute {attr_name} doesnt exist"
            )
            
           
        else:
            val = self.env.get(var_name)
            
            if val is not None:
                return val
            closure = self.__get_func_by_name(var_name, None)
            if closure is None:
                super().error(
                    ErrorType.NAME_ERROR, f"Variable/function {var_name} not found"
                )
            return Value(Type.CLOSURE, closure)

    

    def __eval_op(self, arith_ast):
        left_value_obj = self.__eval_expr(arith_ast.get("op1"))
        right_value_obj = self.__eval_expr(arith_ast.get("op2"))

        left_value_obj, right_value_obj = self.__bin_op_promotion(
            arith_ast.elem_type, left_value_obj, right_value_obj
        )

        if not self.__compatible_types(
            arith_ast.elem_type, left_value_obj, right_value_obj
        ):
            super().error(
                ErrorType.TYPE_ERROR,
                f"Incompatible types for {arith_ast.elem_type} operation",
            )
        if arith_ast.elem_type not in self.op_to_lambda[left_value_obj.type()]:
            super().error(
                ErrorType.TYPE_ERROR,
                f"Incompatible operator {arith_ast.elem_type} for type {left_value_obj.type()}",
            )
        f = self.op_to_lambda[left_value_obj.type()][arith_ast.elem_type]
        return f(left_value_obj, right_value_obj)

    # bool and int, int and bool for and/or/==/!= -> coerce int to bool
    # bool and int, int and bool for arithmetic ops, coerce true to 1, false to 0
    def __bin_op_promotion(self, operation, op1, op2):
        if operation in self.op_to_lambda[Type.BOOL]:  # && or ||
            
            # If this operation is still allowed in the ints, then continue
            if operation in self.op_to_lambda[Type.INT] and op1.type() == Type.INT \
                and op2.type() == Type.INT:
                pass
            else:
                if op1.type() == Type.INT:
                    op1 = Interpreter.__int_to_bool(op1)
                if op2.type() == Type.INT:
                    op2 = Interpreter.__int_to_bool(op2)
        if operation in self.op_to_lambda[Type.INT]:  # +, -, *, /
            if op1.type() == Type.BOOL:
                op1 = Interpreter.__bool_to_int(op1)
            if op2.type() == Type.BOOL:
                op2 = Interpreter.__bool_to_int(op2)
        return (op1, op2)

    def __unary_op_promotion(self, operation, op1):
        if operation == "!" and op1.type() == Type.INT:
            op1 = Interpreter.__int_to_bool(op1)
        return op1

    @staticmethod
    def __int_to_bool(value):
        return Value(Type.BOOL, value.value() != 0)

    @staticmethod
    def __bool_to_int(value):
        return Value(Type.INT, 1 if value.value() else 0)

    def __compatible_types(self, oper, obj1, obj2):
        # DOCUMENT: allow comparisons ==/!= of anything against anything
        if oper in ["==", "!="]:
            return True
        return obj1.type() == obj2.type()

    def __eval_unary(self, arith_ast, t, f):
        value_obj = self.__eval_expr(arith_ast.get("op1"))
        value_obj = self.__unary_op_promotion(arith_ast.elem_type, value_obj)

        if value_obj.type() != t:
            super().error(
                ErrorType.TYPE_ERROR,
                f"Incompatible type for {arith_ast.elem_type} operation",
            )
        return Value(t, f(value_obj.value()))

    def __setup_ops(self):
        self.op_to_lambda = {}
        # set up operations on integers
        self.op_to_lambda[Type.INT] = {}
        self.op_to_lambda[Type.INT]["+"] = lambda x, y: Value(
            x.type(), x.value() + y.value()
        )
        self.op_to_lambda[Type.INT]["-"] = lambda x, y: Value(
            x.type(), x.value() - y.value()
        )
        self.op_to_lambda[Type.INT]["*"] = lambda x, y: Value(
            x.type(), x.value() * y.value()
        )
        self.op_to_lambda[Type.INT]["/"] = lambda x, y: Value(
            x.type(), x.value() // y.value()
        )
        self.op_to_lambda[Type.INT]["=="] = lambda x, y: Value(
            Type.BOOL, x.value() == y.value()
        )
        self.op_to_lambda[Type.INT]["!="] = lambda x, y: Value(
            Type.BOOL, x.value() != y.value()
        )
        self.op_to_lambda[Type.INT]["<"] = lambda x, y: Value(
            Type.BOOL, x.value() < y.value()
        )
        self.op_to_lambda[Type.INT]["<="] = lambda x, y: Value(
            Type.BOOL, x.value() <= y.value()
        )
        self.op_to_lambda[Type.INT][">"] = lambda x, y: Value(
            Type.BOOL, x.value() > y.value()
        )
        self.op_to_lambda[Type.INT][">="] = lambda x, y: Value(
            Type.BOOL, x.value() >= y.value()
        )
        #  set up operations on strings
        self.op_to_lambda[Type.STRING] = {}
        self.op_to_lambda[Type.STRING]["+"] = lambda x, y: Value(
            x.type(), x.value() + y.value()
        )
        self.op_to_lambda[Type.STRING]["=="] = lambda x, y: Value(
            Type.BOOL, x.value() == y.value()
        )
        self.op_to_lambda[Type.STRING]["!="] = lambda x, y: Value(
            Type.BOOL, x.value() != y.value()
        )
        #  set up operations on bools
        self.op_to_lambda[Type.BOOL] = {}
        self.op_to_lambda[Type.BOOL]["&&"] = lambda x, y: Value(
            x.type(), x.value() and y.value()
        )
        self.op_to_lambda[Type.BOOL]["||"] = lambda x, y: Value(
            x.type(), x.value() or y.value()
        )
        self.op_to_lambda[Type.BOOL]["=="] = lambda x, y: Value(
            Type.BOOL, x.value() == y.value()
        )
        self.op_to_lambda[Type.BOOL]["!="] = lambda x, y: Value(
            Type.BOOL, x.value() != y.value()
        )

        #  set up operations on nil
        self.op_to_lambda[Type.NIL] = {}
        self.op_to_lambda[Type.NIL]["=="] = lambda x, y: Value(
            Type.BOOL, x.value() == y.value()
        )
        self.op_to_lambda[Type.NIL]["!="] = lambda x, y: Value(
            Type.BOOL, x.value() != y.value()
        )

        #  set up operations on closures
        self.op_to_lambda[Type.CLOSURE] = {}
        self.op_to_lambda[Type.CLOSURE]["=="] = lambda x, y: Value(
            Type.BOOL, x.value() == y.value()
        )
        self.op_to_lambda[Type.CLOSURE]["!="] = lambda x, y: Value(
            Type.BOOL, x.value() != y.value()
        )
        
        # set up operations on objects
        self.op_to_lambda[Type.OBJECT] = {}
        self.op_to_lambda[Type.OBJECT]["=="] = lambda x, y: Value(
            Type.BOOL, x.value() == y.value()
        )
        self.op_to_lambda[Type.OBJECT]["!="] = lambda x, y: Value(
            Type.BOOL, x.value() != y.value()
        )

    def __do_if(self, if_ast):
        cond_ast = if_ast.get("condition")
        result = self.__eval_expr(cond_ast)
        if result.type() == Type.INT:
            result = Interpreter.__int_to_bool(result)
        if result.type() != Type.BOOL:
            super().error(
                ErrorType.TYPE_ERROR,
                "Incompatible type for if condition",
            )
        if result.value():
            statements = if_ast.get("statements")
            status, return_val = self.__run_statements(statements)
            return (status, return_val)
        else:
            else_statements = if_ast.get("else_statements")
            if else_statements is not None:
                status, return_val = self.__run_statements(else_statements)
                return (status, return_val)

        return (ExecStatus.CONTINUE, Interpreter.NIL_VALUE)

    def __do_while(self, while_ast):
        cond_ast = while_ast.get("condition")
        run_while = Interpreter.TRUE_VALUE
        while run_while.value():
            run_while = self.__eval_expr(cond_ast)
            if run_while.type() == Type.INT:
                run_while = Interpreter.__int_to_bool(run_while)
            if run_while.type() != Type.BOOL:
                super().error(
                    ErrorType.TYPE_ERROR,
                    "Incompatible type for while condition",
                )
            if run_while.value():
                statements = while_ast.get("statements")
                status, return_val = self.__run_statements(statements)
                if status == ExecStatus.RETURN:
                    return status, return_val

        return (ExecStatus.CONTINUE, Interpreter.NIL_VALUE)

    def __do_return(self, return_ast):
        expr_ast = return_ast.get("expression")
        if expr_ast is None:
            return (ExecStatus.RETURN, Interpreter.NIL_VALUE)
        value_obj = copy.deepcopy(self.__eval_expr(expr_ast))
        return (ExecStatus.RETURN, value_obj)

def main():
    interpreter = Interpreter()
    program1 = """

func main() {
  a = @;
  a.x = 2;
  b = @;
  b.proto = a;
  a.lam = lambda() {
    if (this.x > 0) {
      this.x = this.x - 1;
      
      print(this.x);
      b.lam();
    }

    test = lambda() {
      
      print(this.x);
    };
    test();
  };
  a.lam();
  
  print(a.x);
}  
    """
    interpreter.run(program1)
    # print(interpreter.variable_name_to_value)


if __name__ == "__main__":
    main()
