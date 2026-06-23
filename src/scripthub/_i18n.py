TRADUCOES: dict[str, str] = {
    # typer.core — metadados inline (modo sem Rich)
    "(dynamic)": "(dinâmico)",
    "Aborted!": "Abortado!",
    "default: {default}": "padrão: {default}",
    "required": "obrigatório",
    "env var: {var}": "var env: {var}",
    "Arguments": "Argumentos",
    "Options": "Opções",
    "Commands": "Comandos",
    # typer.core — erros de comando
    "Missing command.": "Comando não fornecido.",
    "No such command {name!r}.": "Comando {name!r} não encontrado.",
}


def _pt_BR(msg: str) -> str:
    return TRADUCOES.get(msg, msg)


def instalar() -> None:
    _patch_rich_utils()
    _patch_typer_core()
    _patch_vendored_click()
    _patch_help_option()
    _patch_completion_options()


def _patch_rich_utils() -> None:
    import typer.rich_utils as _ru

    _ru.DEPRECATED_STRING = "(obsoleto) "
    _ru.DEFAULT_STRING = "[padrão: {}]"
    _ru.ENVVAR_STRING = "[var env: {}]"
    _ru.REQUIRED_LONG_STRING = "[obrigatório]"
    _ru.ARGUMENTS_PANEL_TITLE = "Argumentos"
    _ru.OPTIONS_PANEL_TITLE = "Opções"
    _ru.COMMANDS_PANEL_TITLE = "Comandos"
    _ru.ERRORS_PANEL_TITLE = "Erro"
    _ru.ABORTED_TEXT = "Abortado."
    _ru.RICH_HELP = (
        "Execute [blue]'{command_path} {help_option}'[/] para obter ajuda."
    )


def _patch_typer_core() -> None:
    import typer.core as _tc

    _tc._ = _pt_BR  # type: ignore[attr-defined]


def _patch_vendored_click() -> None:
    import typer._click.exceptions as _ce
    import typer._click.formatting as _cf

    # HelpFormatter.write_usage — "Usage: " → "Uso: "
    _orig_write_usage = _cf.HelpFormatter.write_usage

    def _write_usage_pt(self, prog: str, args: str = "", prefix: str | None = None) -> None:  # type: ignore[misc]
        if prefix is None:
            prefix = "Uso: "
        _orig_write_usage(self, prog, args, prefix)

    _cf.HelpFormatter.write_usage = _write_usage_pt  # type: ignore[method-assign]

    # ClickException.show — "Error: ..." → "Erro: ..."
    def _click_exception_show_pt(self, file=None) -> None:  # type: ignore[misc]
        import sys
        from typer._click.utils import echo

        if file is None:
            file = sys.stderr
        echo(f"Erro: {self.format_message()}", file=file, color=self.show_color)

    _ce.ClickException.show = _click_exception_show_pt  # type: ignore[method-assign]

    # UsageError.show — "Error: ..." e "Try ... for help." → pt-BR
    def _usage_error_show_pt(self, file=None) -> None:  # type: ignore[misc]
        import sys
        from typer._click.utils import echo

        if file is None:
            file = sys.stderr
        color = None
        hint = ""
        if self.ctx is not None and self.ctx.command.get_help_option(self.ctx) is not None:
            command = self.ctx.command_path
            option = self.ctx.help_option_names[0]
            hint = f"Execute '{command} {option}' para obter ajuda.\n"
        if self.ctx is not None:
            color = self.ctx.color
            echo(f"{self.ctx.get_usage()}\n{hint}", file=file, color=color)
        echo(f"Erro: {self.format_message()}", file=file, color=color)

    _ce.UsageError.show = _usage_error_show_pt  # type: ignore[method-assign]

    # BadParameter.format_message — "Invalid value" → "Valor inválido"
    def _bad_param_format_pt(self) -> str:  # type: ignore[misc]
        from typer._click.exceptions import _join_param_hints

        if self.param_hint is not None:
            param_hint = self.param_hint
        elif self.param is not None:
            param_hint = self.param.get_error_hint(self.ctx)  # type: ignore[arg-type]
        else:
            return f"Valor inválido: {self.message}"
        hint = _join_param_hints(param_hint)
        return f"Valor inválido para {hint}: {self.message}"

    _ce.BadParameter.format_message = _bad_param_format_pt  # type: ignore[method-assign]

    # MissingParameter.format_message — "Missing argument/option/parameter" → pt-BR
    def _missing_param_format_pt(self) -> str:  # type: ignore[misc]
        from typer._click.exceptions import _join_param_hints

        if self.param_hint is not None:
            param_hint = self.param_hint
        elif self.param is not None:
            param_hint = self.param.get_error_hint(self.ctx)  # type: ignore[arg-type]
        else:
            param_hint = None

        param_hint_str = _join_param_hints(param_hint)
        param_hint_str = f" {param_hint_str}" if param_hint_str else ""

        param_type = self.param_type
        if param_type is None and self.param is not None:
            param_type = self.param.param_type_name

        msg = self.message
        if self.param is not None:
            msg_extra = self.param.type.get_missing_message(param=self.param, ctx=self.ctx)
            if msg_extra:
                msg = f"{msg}. {msg_extra}" if msg else msg_extra

        msg = f" {msg}" if msg else ""

        if param_type == "argument":
            missing = "Argumento ausente"
        elif param_type == "option":
            missing = "Opção ausente"
        elif param_type == "parameter":
            missing = "Parâmetro ausente"
        else:
            missing = f"{param_type} ausente" if param_type else "Parâmetro ausente"

        return f"{missing}{param_hint_str}.{msg}"

    _ce.MissingParameter.format_message = _missing_param_format_pt  # type: ignore[method-assign]

    # MissingParameter.__str__ — "Missing parameter: ..." → pt-BR
    def _missing_param_str_pt(self) -> str:  # type: ignore[misc]
        if not self.message:
            param_name = self.param.name if self.param else None
            return f"Parâmetro ausente: {param_name}"
        return self.message

    _ce.MissingParameter.__str__ = _missing_param_str_pt  # type: ignore[method-assign]

    # NoSuchOption — mensagem gerada no __init__ quando message=None
    _orig_no_such_init = _ce.NoSuchOption.__init__

    def _no_such_option_init_pt(self, option_name: str, message: str | None = None, possibilities=None, ctx=None) -> None:  # type: ignore[misc]
        if message is None:
            message = f"Opção inválida: {option_name}"
        _orig_no_such_init(self, option_name, message, possibilities, ctx)

    _ce.NoSuchOption.__init__ = _no_such_option_init_pt  # type: ignore[method-assign]


def _patch_help_option() -> None:
    import typer._click.decorators as _dec
    from typer._click.utils import echo

    def _help_option_pt(param_decls: list[str]):  # type: ignore[misc]
        def show_help(ctx, _param, value: bool) -> None:  # type: ignore[misc]
            if value and not ctx.resilient_parsing:
                echo(ctx.get_help(), color=ctx.color)
                ctx.exit()

        from typer._click.decorators import option

        return option(
            param_decls,
            is_flag=True,
            expose_value=False,
            is_eager=True,
            help="Exibir esta mensagem e sair.",
            callback=show_help,
            required=False,
        )

    _dec.help_option = _help_option_pt  # type: ignore[attr-defined]


def _patch_completion_options() -> None:
    import inspect
    import typer.completion as _tc

    sig = inspect.signature(_tc._install_completion_placeholder_function)
    params = list(sig.parameters.values())
    params[0].default.help = "Instalar completação para o shell atual."
    params[1].default.help = "Exibir completação para o shell atual."
