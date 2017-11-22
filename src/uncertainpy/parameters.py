import re
import fileinput
import sys
import collections

import chaospy as cp


__all__ = ["Parameters", "Parameter"]

class Parameter(object):
    """
    Parameter object, contains name of parameter, value of parameter and distribution of parameter.

    Parameters
    ----------
    name: str
        Name of the parameter.
    value: float, int, None
        The fixed value of the parameter. If you give a parameter a distribution,
        in most cases you do not need to give it a fixed value.
    distribution: {None, Chaospy distribution, Function that returns a Chaospy distribution}, optional
        The distribution of the parameter. A parameter is considered uncertain
        if it has a distribution.
        Defaults to None.


    Attributes
    ----------
    name: str
        Name of the parameter.
    value: float, int
        The value of the parameter.
    distribution : uncertainpy.Parameter.distribution
        The distribution of the parameter. A parameter is considered uncertain
        if it has a distribution.
    """

    def __init__(self, name, value, distribution=None):
        """
        Parameter object, contains name of parameter, value of parameter and distribution of parameter.

        Parameters
        ----------
        name: str
            Name of the parameter.
        value: float, int, None
            The fixed value of the parameter. If you give a parameter a distribution,
            in most cases you do not need to give it a fixed value.
        distribution: {None, Chaospy distribution, Function that returns a Chaospy distribution}, optional
            The distribution of the parameter. A parameter is considered uncertain
            if it has a distribution.
            Defaults to None.
        """

        self.name = name
        self.value = value

        self._distribution = None

        self.distribution = distribution


    @property
    def distribution(self):
        """
        A Chaospy distribution or a function that returns a Chaospy distribution.
        If None the parameter has no distribution and is not considered uncertain.

        Parameters
        ----------
        distribution: {None, Chaospy distribution, Function that returns a Chaospy distribution}, optional
            The distribution of the parameter, used if the parameter is uncertain.
            Defaults to None.

        Returns
        -------
        distribution: {Chaospy distribution, None}
            The distribution of the parameter, if None the
            parameter has no distribution and is not considered uncertain.
        """
        return self._distribution

    @distribution.setter
    def distribution(self, new_distribution):
        if new_distribution is None:
            self._distribution = None
        elif isinstance(new_distribution, cp.Dist):
            self._distribution = new_distribution
        elif hasattr(new_distribution, '__call__'):
            self._distribution = new_distribution(self.value)
            if not isinstance(self._distribution, cp.Dist):
                raise TypeError("Function new_distribution does not return a Chaospy distribution")
        else:
            raise TypeError("new_distribution is neither a function nor a Chaospy distribution")



    def set_parameter_file(self, filename, value):
        """
        Set parameters to given value in a parameter file.

        Search `filename` for occurrences of ``name = number``
        and replace ``number`` with `value`.

        Parameters
        ----------
        filename: str
            Name of file.
        value: float, int
            New value to set in parameter file.
        """
        search_string = r"(\A|\b)(" + self.name + r")(\s*=\s*)((([+-]?\d+[.]?\d*)|([+-]?\d*[.]?\d+))([eE][+-]?\d+)*)($|\b)"
        pattern = re.compile(search_string)

        for line in fileinput.input(filename, inplace=True):
            sys.stdout.write(pattern.sub(r"\g<1>\g<2>\g<3>" + str(value), line))


    def reset_parameter_file(self, filename):
        """
        Set all parameters to the original value in the parameter file, `filename`.

        Parameters
        ----------
        filename: str
            Name of file.
        """
        self.set_parameter_file(filename, self.value)


    def __str__(self):
        """
        Return a readable string describing the parameter.

        Returns
        -------
        str
            A string containing ``name``, ``value``, and if a parameter is uncertain.
        """
        if self.distribution is None:
            uncertain = ""
        else:
            uncertain = " - Uncertain"

        return "{parameter}: {value}{uncertain}".format(parameter=self.name, value=self.value, uncertain=uncertain)





class Parameters(collections.MutableMapping):
    """
    A collection of parameters.

    Has all standard dictionary methods implemented, such as items, value, contains and similar implemented.

    Parameters
    ----------
    parameterlist: {list of Parameter instances, list [[name, value, distribution],...]}
        List the parameters that should be created.
        On the form: ``parameterlist = [ParameterObject1, ParameterObject2, ...]``
        Or: ``parameterlist = [[name1, value1, distribution1], ...]``, where
        the arguments are similar to the arguments given to Parameter().
    distribution: {None, multivariate Chaospy distribution}, optional
        A multivariate distribution of all parameters, if it exists, it is used
        instead of individual distributions.
        Defaults to None.


    Attributes
    ----------
    parameters: dict
        A dictionary of parameters with ``name`` as key and Parameter object as value.
    distribution: {None, multivariate Chaospy distribution}, optional
        A multivariate distribution of all parameters, if it exists, it is used
        instead of individual distributions.
        Defaults to None.

    See Also
    --------
    uncertainpy.Parameter : Parameter class
    """

    def __init__(self, parameterlist=[], distribution=None):
        """
        A collection of parameters.

        Implements collections.MutableMapping, and have all dictionary methods.

        Parameters
        ----------
        parameterlist: {list of Parameter instances, list [[name, value, distribution],...]}, optional
            List the parameters that should be created.
            On the form: ``parameterlist = [ParameterObject1, ParameterObject2, ...]``
            Or: ``parameterlist = [[name1, value1, distribution1], ...]``, where
            the arguments are similar to the arguments given to Parameter().
            Default is an empty list.

        See Also
        --------
        uncertainpy.Parameter : Parameter object
        """
        self.parameters = collections.OrderedDict()
        self.distribution = distribution

        try:
            for i in parameterlist:
                if isinstance(i, Parameter):
                    self.parameters[i.name] = i
                else:
                    self.parameters[i[0]] = Parameter(*i)
        except TypeError as error:
            msg = "parameters must be either list of Parameter objects or list [[name, value, distribution], ...]"
            if not error.args:
                error.args = ("",)
            error.args = error.args + (msg,)
            raise


    def __getitem__(self, name):
        """
        Return Parameter object with `name`.

        Parameters
        ----------
        name: str
            Name of parameter.

        Returns
        -------
        Parameter object
            The parameter object with `name`.
        """
        return self.parameters[name]


    def __iter__(self):
        """
        Iterate over the parameter objects.

        Yields
        ------
        Parameter object
            A parameter object.
        """

        return iter(self.parameters.values())

    def __str__(self):
        """
        Convert all parameters to a readable string.

        Returns
        -------
        str
           A readable string of all parameter objects.
        """
        result = ""
        for name in sorted(self.parameters.keys()):
            result += str(self.parameters[name]) + "\n"

        return result.strip()


    def __len__(self):
        """
        Get the number of parameters.

        Returns
        -------
        int
            The number of parameters.
        """
        return len(self.parameters)


    def __setitem__(self, name, parameter):
        """
        Set parameter with `name`.

        Parameters
        ----------
        name: str
            Name of parameter.
        parameter: Parameter object
            The parameter object of `name`.
        """

        if not isinstance(parameter, Parameter):
            raise ValueError("parameter must be an instance of Parameter")
        self.parameters[name] = parameter


    def __delitem__(self, name):
        """
        Delete parameter with `name`.

        Parameters
        ----------
        name: str
            Name of parameter.
        """

        del self.parameters[name]


    def set_distribution(self, parameter, distribution):
        """
        Set the distribution of a parameter.

        Parameters
        ----------
        parameter: str
            Name of parameter.
        distribution: {None, Chaospy distribution, Function that returns a Chaospy distribution}
            The distribution of the parameter.
        """
        self.parameters[parameter].distribution = distribution


    def set_all_distributions(self, distribution):
        """
        Set the distribution of all parameters.

        Parameters
        ----------
        distribution: {None, Chaospy distribution, Function that returns a Chaospy distribution}
            The distribution of the parameter.
        """
        for parameter in self.parameters:
            self.parameters[parameter].distribution = distribution


    def get_from_uncertain(self, attribute="name"):
        """
        Return attributes from uncertain parameters.

        Return a list of attributes (``name``, ``value``, or ``distribution``) from
        each uncertain parameters (parameters that have a distribution).

        Parameters
        ----------
        attribute: {"name", "value", "distribution"}, optional
            The name of the attribute to be returned from each uncertain parameter.
            Default is `name`.

        Returns
        -------
        list
            List containing the `attribute` of each uncertain parameters.
        """

        items = []
        for parameter in self.parameters.values():
            if parameter.distribution is not None:
                items.append(getattr(parameter, attribute))
        return items


    def get(self, attribute="name", parameter_names=None):
        """
        Return attributes from all parameters.

        Return a list of attributes (``name``, ``value``, or ``distribution``) from
        each parameters (parameters that have a distribution).

        Parameters
        ----------
        attribute: {"name", "value", "distribution"}, optional
            The name of the attribute to be returned from each uncertain parameter. Default is `name`.
        parameter_names: {None, list, str}, optional
            A list of all parameters of which attribute should be returned,
            or a string for a single parameter.
            If None, the attribute all parameters are returned.
            Default is None.

        Returns
        -------
        list
            List containing the `attribute` of each parameters.
        """

        if parameter_names is None:
            parameter_names = self.parameters.keys()

        if isinstance(parameter_names, str):
            parameter_names = [parameter_names]

        return_parameters = []
        for parameter_name in parameter_names:
            return_parameters.append(self.parameters[parameter_name])

        return [getattr(parameter, attribute) for parameter in return_parameters]


    def set_parameters_file(self, filename, parameters):
        """
        Set listed parameters to their value in a parameter file.

        For each parameter listed in `parameters`, search `filename` for occurrences of
        ``parameter_name = number`` and replace ``number`` with value of that parameter.

        Parameters
        ----------
        filename: str
            Name of file.
        parameters: list
            List of parameter names.
        """
        for parameter in parameters:
            self.parameters[parameter].set_parameter_file(filename, parameters[parameter])


    def reset_parameter_file(self, filename):
        """
        Set all parameters to their value in a parameter file.

        For all parameters, search `filename` for occurrences of
        ``parameter_name = number`` and replace ``number`` with value of that parameter.

        Parameters
        ----------
        filename: str
            Name of file.
        """
        for parameter in self.parameters:
            self.parameters[parameter].set_parameter_file(filename, self.parameters[parameter].value)
