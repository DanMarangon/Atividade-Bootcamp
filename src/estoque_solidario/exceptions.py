class ValidationError(ValueError):
    """Erro para entradas inválidas informadas pelo usuário."""


class BusinessRuleError(ValueError):
    """Erro para violações de regra de negócio."""
