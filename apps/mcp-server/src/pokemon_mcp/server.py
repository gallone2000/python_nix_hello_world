import os
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastmcp import FastMCP

from pokemon_mcp.pokemon_api import (
    close_http_client,
    compare_pokemon_data,
    get_evolution_chain_data,
    get_pokemon_by_type,
    get_pokemon_data,
    get_pokemon_species_data,
    get_type_matchup_data,
    search_pokemon_data,
)


@asynccontextmanager
async def lifespan(_: FastMCP) -> AsyncIterator[dict]:
    try:
        yield {}
    finally:
        await close_http_client()


mcp = FastMCP("pokemon-mcp", lifespan=lifespan)


@mcp.tool
async def get_pokemon(name_or_id: str) -> dict:
    """
    Get a Pokemon by name or id.

    Use this when the user asks for details about a specific Pokemon.
    """
    pokemon = await get_pokemon_data(name_or_id)
    return pokemon.model_dump()


@mcp.tool
async def get_pokemon_species(name_or_id: str) -> dict:
    """
    Get species-level information for a Pokemon by name or id.

    Use this tool when the user asks for Pokedex description, genus, habitat,
    color, shape, or whether a Pokemon is legendary or mythical.
    """
    species = await get_pokemon_species_data(name_or_id)
    return species.model_dump()


@mcp.tool
async def search_pokemon(query: str, limit: int | None = 10) -> dict:
    """
    Search Pokemon by partial name.

    Ranking priority:
    1. exact match
    2. prefix match
    3. substring match

    Returns richer search results including Pokemon id and image URL.
    """
    result = await search_pokemon_data(query, limit=limit)
    return result.model_dump()


@mcp.tool
async def list_pokemon_by_type(type_name: str, limit: int | None = 10) -> dict:
    """
    List Pokemon names that belong to a given type.

    Use this tool when the user asks for examples or a list of Pokemon of a type,
    not for battle strengths or weaknesses.

    Args:
        type_name: Pokemon type name, for example 'electric' or 'fire'.
        limit: Maximum number of Pokemon names to return.
    """
    safe_limit = 10 if limit is None else max(1, min(limit, 50))
    result = await get_pokemon_by_type(type_name, limit=safe_limit)
    return result.model_dump()


@mcp.tool
async def get_type_matchup(type_name: str) -> dict:
    """
    Get the battle strengths, weaknesses, resistances, and immunities for a Pokemon type.

    Use this tool when the user asks what a type is strong against, weak against,
    resistant to, or immune to.
    """
    result = await get_type_matchup_data(type_name)
    return result.model_dump()


@mcp.tool
async def get_evolution_chain(name_or_id: str) -> dict:
    """
    Get the evolution chain for a Pokemon by name or id.

    Use this tool when the user asks how a Pokemon evolves or what its
    full evolution line is.
    """
    result = await get_evolution_chain_data(name_or_id)
    return result.model_dump()


@mcp.tool
async def compare_pokemon(pokemon_1: str, pokemon_2: str) -> dict:
    """
    Compare two Pokemon by types, abilities, and base stats.

    Use this tool when the user asks to compare two Pokemon or asks which one
    is faster, stronger, bulkier, or generally better in raw stats.
    """
    result = await compare_pokemon_data(pokemon_1, pokemon_2)
    return result.model_dump()


def main() -> None:
    transport = os.getenv("MCP_TRANSPORT", "stdio").strip().lower()

    if transport == "http":
        host = os.getenv("MCP_HOST", "0.0.0.0")
        port = int(os.getenv("MCP_PORT", "8000"))
        mcp.run(transport="http", host=host, port=port)
        return

    if transport == "sse":
        host = os.getenv("MCP_HOST", "0.0.0.0")
        port = int(os.getenv("MCP_PORT", "8000"))
        mcp.run(transport="sse", host=host, port=port)
        return

    mcp.run()


if __name__ == "__main__":
    main()