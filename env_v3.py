from type_valuev3 import Type, Value

# The EnvironmentManager class keeps a mapping between each variable name (aka symbol)
# in a brewin program and the Value object, which stores a type, and a value.
class EnvironmentManager:
    def __init__(self):
        self.environment = [{}]

    # returns a VariableDef object
    def get(self, symbol):
        print(f"env::get(): for {symbol}")
        for env in reversed(self.environment):
            if symbol in env:
                return env[symbol]

        return None

    def set(self, symbol, value, force_new_var_creation=False):
        if force_new_var_creation:
            self.environment[-1][symbol] = value
            return

        for env in reversed(self.environment):
            if symbol in env:
                env[symbol] = value
                return

        # symbol not found anywhere in the environment
        self.environment[-1][symbol] = value

    # create a new symbol in the top-most environment, regardless of whether that symbol exists
    # in a lower environment
    def create(self, symbol, value):
        self.environment[-1][symbol] = value

    # used when we enter a nested block to create a new environment for that block
    def push(self, env = None):
        if env is None:
            self.environment.append({})  # [{}] -> [{}, {}]
        else:
            self.environment.append(env)

    # used when we exit a nested block to discard the environment for that block
    def pop(self):
        self.environment.pop()

    def __enumerate(self):
        captured_so_far = set()
        for captured in reversed(self.environment):
            for var_name, value in captured.items():
                if var_name in captured_so_far:
                    continue
                captured_so_far.add(var_name)
                yield (var_name, value)

    def __iter__(self):
        return self.__enumerate()


    def print_stack(self):
        print("Current call stack:")
        # for i, frame in enumerate(reversed(self.environment)):
        #     print(f"Frame {len(self.environment) - i}: {frame}")

        # print("Current call stack (not in reverse):")
        # for i, frame in enumerate(self.environment):
        #     print(f"Frame {len(self.environment) - i}: {frame}")
        for i, frame in enumerate(reversed(self.environment), start=1):
            print(f"    Frame {i}::")
            for var, value in frame.items():
                if value is not None:
                    if value.type() == Type.OBJECT:
                        print(f"        var is: {var}; value type is {value.type()}")
                        obj_content = value.value()
                        print("         fields:")
                        for attr_name, content in obj_content.field.items():
                            print(f"            {attr_name}:{content.type()}:{content.value()}")
                        print("         methods:")
                        for attr_name, content in obj_content.method.items():
                            print(f"            {attr_name}:{content.type()}:{content.value()}")
                    else:
                        print(f"        var is: {var}; value type is {value.type()}")
                else:

                    print(f"        var is: {var}; value is {value}")
                # if value.type() == Type.LAMB:
                #     print(f"        {var}: Lambda Closure")
                #     funct_ast_val = value.value()
                #     print(f"            func_ast: {funct_ast_val['func_ast']}")

                #     captured_env = funct_ast_val['captured_env']
                #     for env_var, env_value in captured_env.items():
                #         actual_env_value = env_value.value() if hasattr(
                #             env_value, 'value') else env_value
                #         # print("entering capture")
                #         print(
                #             f"            Captured Env - {env_var}: {actual_env_value}")
                # else:
                #     actual_value = value.value() if hasattr(value, 'value') else value
                #     if isinstance(actual_value, int) or isinstance(actual_value, str):

                #         print(
                #             f"        int/str:{var}:{actual_value}; id: {id(value)}")
                #     else:
                #         print(f"        non-int:{var}:{actual_value}")
                #         if isinstance(actual_value, dict):
                #             for key, val in actual_value.items():
                #                 print(
                #                     f"        the key is: {key}; the value is: {val}")
