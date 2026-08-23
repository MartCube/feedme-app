"""One error body for the whole API: {"detail": "..."}.

ninja already answers 401 and 404 in this shape — AuthenticationError and Http404 both
subclass HttpError, whose default handler emits {"detail": str(exc)}. Validation is the
odd one out (its detail is a list of pydantic dicts), so only that one is reshaped here.
Keeping the contract single-shaped keeps T6's generated TypeScript to one error type.
"""

from ninja import Schema
from ninja.errors import ValidationError


class ErrorSchema(Schema):
    detail: str


def register_error_handlers(api):
    @api.exception_handler(ValidationError)
    def validation_error(request, exc):
        detail = '; '.join(
            f'{".".join(str(part) for part in error["loc"])}: {error["msg"]}'
            for error in exc.errors
        )
        return api.create_response(request, {'detail': detail or 'Invalid input'}, status=422)
