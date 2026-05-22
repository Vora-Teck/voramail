import click
from flask.cli import with_appcontext
from werkzeug.security import generate_password_hash
from root.extensions import db
from root.models import User, UserRole


@click.command("createsuperuser")
@click.option("--email", prompt=True, help="Superuser email")
@click.option(
    "--password",
    prompt=True,
    hide_input=True,
    confirmation_prompt=True,
    help="Superuser password"
)
@with_appcontext
def create_superuser(email, password):
    if User.query.filter_by(email=email).first():
        click.echo("❌ User already exists")
        return

    user = User(
        email=email,
        role=UserRole.superuser,
        password=generate_password_hash(password)
    )

    db.session.add(user)
    db.session.commit()

    click.echo("✅ Superuser created successfully")
    #click.echo(f"Public Key: {public_key}")
    #click.echo(f"Secret Key (store securely): {secret_key}")
