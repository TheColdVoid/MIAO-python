import inspect
from typing import List

available_return_type = [str, int, list, dict, object, bool]


def to_camel_case(snake_str):
    components = snake_str.split('_')
    return components[0] + ''.join(x.title() for x in components[1:])


def filter_dict(dict: dict, ignore_keys=[]):
    return {k: v for k, v in dict.items() if k not in ignore_keys}


def key_to_camel_case(dict):
    return {to_camel_case(k): v for k, v, in dict.items()}


TYPENAME_TABLE: {type: str} = {
    int: "number",
    str: "string",
    bool: "bool",
    object: "object",
    # if type is not exist,use string as default type
    inspect.Signature.empty: "str"

}


def to_js_typename(python_type: type):
    # TODO:Add support for more detailed numeric types, such as support for more detailed display of real numbers and integers, etc.
    if python_type in TYPENAME_TABLE:
        return TYPENAME_TABLE[python_type]
    else:
        raise RuntimeError("unsupported type %s" % str(type))


def get_attrs(clazz):
    return [k for k in clazz.__dict__.keys()
            if not k.startswith('__')
            and not k.endswith('__')
            and not k.startswith('_')
            ]


# Base class for all classes to be serialized to json, with get_dict method
class Info:
    def get_dict(self):
        return self.__dict__


class ParameterInfo(Info):

    def __init__(self,
                 name: str = None,
                 type_name: str = None,
                 display_name: str = None) -> None:
        self.name: str = name
        self.type_name: str = type_name
        self.display_name: str = display_name

    def get_dict(self):
        # In order to generate a uniform format of json, so here the key name is converted to lowerCamelCase
        dict = self.__dict__
        dict = key_to_camel_case(dict)
        return dict


class Visualization():

    def __init__(self):
        self.type = None

    def get_dict(self):
        # In order to generate a uniform format of json, so here the key name is converted to lowerCamelCase
        dict = self.__dict__
        dict = key_to_camel_case(dict)
        return dict


class TableVisualization(Visualization):

    def __init__(self):
        super().__init__()
        self.headers: List[str] = None
        self.is_basic_list: bool = False
        self.is_custom_class: bool = False


class MethodInfo(Info):
    def __init__(self,
                 func=None,
                 parameter_infos: List[ParameterInfo] = [],
                 name: str = None,
                 description: str = None,
                 display_name: str = None,
                 hashcode: int = None,
                 visualization: Visualization = None,
                 ) -> None:
        self.name: str = name
        self.description: str = description
        self.display_name: str = display_name
        self.hashcode: int = hashcode
        self.parameter_infos: List[ParameterInfo] = parameter_infos
        self.func = func
        self.visualization = visualization

    def get_dict(self):
        dict = filter_dict(self.__dict__, ['func'])
        # In order to generate a uniform format of json, so here the key name is converted to lowerCamelCase
        dict = key_to_camel_case(dict)
        return dict


# hashcode -> MethodInfo
DEMOS: {int: MethodInfo} = {}


def print_loading_tips():
    # print loading tips when first registering start
    if len(DEMOS) == 0:
        print("MIAO is scanning and registering functions...")


# param param_name is the actual name of each parameter
# to be displayed, passed in turn.
# If it is None or [],
# the name of the parameter is displayed in the UI instead,
# and if the length is less than the number of parameters,
# the parameter is selected from the beginning to the end
# to fit the name.
#
# The visualization option can be set to 'table' or None.
# If it is set to 'Table', then you must return a value of
# type List[dict] or List[CustomClass] or List[Union[str,int,bool]],
# where CustomClass is your own defined Class.
# If there is a possibility of returning empty results,
# then it is recommended that you specify the table headers
# of the returned results in the table_headers parameter.
# Of course, you can also create a class that inherits
# from TypedDict (available only for versions above Python) and
# mark this class with TypeHint on the function return value type to
# have the result of specifying the List[dict] type of the returned result
# table header.
def web_demo(name: str = None,
             description: str = None,
             param_names: List[str] = [],
             visualization: str = None,
             table_headers=None,
             ):
    def register_demo(func):
        print_loading_tips()

        # process function signature
        sig = inspect.signature(func)
        # get parameter's type and name
        params = [sig.parameters[param_name] for param_name in sig.parameters]
        param_infos = []
        for index, param in enumerate(params):
            param_info = ParameterInfo()
            param_info.type_name = to_js_typename(param.annotation)
            param_info.name = param.name
            if index < len(param_names):
                param_info.display_name = param_names[index]
            param_infos.append(param_info)
        method_info = MethodInfo()
        method_info.description = description
        method_info.name = func.__code__.co_name
        method_info.display_name = name
        method_info.func = func
        method_info.hashcode = id(func)
        method_info.parameter_infos = param_infos

        # process visualization option
        if visualization != None:
            if visualization == 'table':
                vis = TableVisualization()
                vis.type = visualization

                if sig.return_annotation != inspect.Signature.empty:
                    # if return value 's type is not List[T] ,skip the type analysis
                    if sig.return_annotation != list and sig.return_annotation._name != 'List':
                        vis.headers = None
                        print(
                            "MIAO Warning:If you want to use Table visualization, then the return value must be of type List[T]")
                    # if typing hint of return value is exist,take its class's attrs as headers
                    # List[T]
                    else:
                        # get type parameter
                        T = sig.return_annotation.__args__[0]
                        # If T is a basic type, set the table type to a basic list type for the interface to provide a targeted presentation
                        if T in available_return_type:
                            vis.headers = None
                            vis.is_basic_list = True
                        # If T is a subclass of TypedDict,get its attrs as headers
                        elif dict in T.__bases__:
                            attrs = list(T.__annotations__.keys())
                            vis.headers = attrs
                            pass
                        # T is a user-defined class that is not a subclass of TypedDict, so no header is set
                        else:
                            vis.headers = None
                            vis.is_custom_class = True
                # if table_headers is exist,take it as headers and overwrite other options
                if table_headers is not None:
                    vis.headers = table_headers
            else:
                raise RuntimeError("unsupported visualization type %s" % visualization)
            method_info.visualization = vis

        DEMOS[method_info.hashcode] = method_info

        def run_demo(*args):
            return func(*args)

        return run_demo

    return register_demo


class HashcodeNotFound(KeyError):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


def call(hashcode, *args):
    if hashcode not in DEMOS:
        raise HashcodeNotFound("hashcode not found")
    demo = DEMOS[hashcode]
    return_value = demo.func(*args)
    if type(return_value) in available_return_type:
        if type(demo.visualization) == TableVisualization:
            if demo.visualization.is_custom_class == True:
                return_value = [item.__dict__ for item in return_value]
        return return_value
    elif hasattr(return_value, '__iter__'):
        return list(return_value)
    elif return_value == None:
        if type(demo.visualization) == TableVisualization:
            return []
    else:
        try:
            return return_value.__dict__
        except:
            raise TypeError("return value type %s is not supported", type(return_value))


def get_scheme() -> [MethodInfo]:
    return list(DEMOS.values())


def print_scheme():
    import json
    print(json.dumps(get_scheme(), default=lambda info: info.get_dict()))
