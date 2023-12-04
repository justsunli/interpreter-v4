from type_valuev4 import Type, Value

# The EnvironmentManager class keeps a mapping between each variable name (aka symbol)
# in a brewin program and the Value object, which stores a type, and a value.
class EnvironmentManager:
    def __init__(self):
        self.environment = [{}]

    # returns a VariableDef object
    def get(self, symbol):
        # print(f"env::get(): for {symbol}")
        for env in reversed(self.environment):
            if symbol in env:
                # print(f"        returning {env[symbol]} to {symbol}")
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

        for i, frame in enumerate(reversed(self.environment), start=1):
            print(f"    Frame {i}::")
            for var, value in frame.items():
                if value is not None:
                    if value.type() == Type.OBJECT:
                        print(f"        var is: {var}; value type is {value.type()}")
                        obj_content = value.value()
                        print("         fields:")
                        for attr_name, content in obj_content.fields.items():
                            print(f"            {attr_name}:{content.type()}:{content.value()}")
                        print("         methods:")
                        for attr_name, content in obj_content.methods.items():
                            print(f"            {attr_name}:{content.type()}:{content.value()}")
                    else:
                        print(f"        var is: {var}; value type is {value.type()}")
                else:

                    print(f"        var is: {var}; value is {value}")
             