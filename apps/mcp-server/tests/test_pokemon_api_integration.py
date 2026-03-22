import pytest

from pokemon_mcp.pokemon_api import (
    compare_pokemon_data,
    get_evolution_chain_data,
    get_pokemon_by_type,
    get_pokemon_data,
    get_pokemon_species_data,
    get_type_matchup_data,
    search_pokemon_data,
)

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]


async def test_get_pokemon_data_pikachu():
    result = await get_pokemon_data("pikachu")

    assert result.name == "pikachu"
    assert result.id == 25
    assert "electric" in result.types
    assert "static" in result.abilities
    assert result.stats.speed == 90
    assert result.image_url is not None


async def test_get_pokemon_by_type_electric():
    result = await get_pokemon_by_type("electric")

    assert result.type == "electric"
    assert result.count == 10
    assert "pikachu" in result.pokemon or len(result.pokemon) == 10


async def test_get_type_matchup_fire():
    result = await get_type_matchup_data("fire")

    assert result.type == "fire"
    assert "grass" in result.double_damage_to
    assert "water" in result.double_damage_from


async def test_get_pokemon_species_pikachu():
    result = await get_pokemon_species_data("pikachu")

    assert result.name == "pikachu"
    assert result.id == 25
    assert isinstance(result.is_legendary, bool)
    assert isinstance(result.is_mythical, bool)


async def test_get_evolution_chain_bulbasaur():
    result = await get_evolution_chain_data("bulbasaur")

    assert result.pokemon == "bulbasaur"
    assert "bulbasaur" in result.chain
    assert "ivysaur" in result.chain
    assert "venusaur" in result.chain


async def test_compare_pokemon_pikachu_vs_raichu():
    result = await compare_pokemon_data("pikachu", "raichu")

    assert result.pokemon_1.name == "pikachu"
    assert result.pokemon_2.name == "raichu"
    assert result.stat_differences.speed is not None


async def test_search_pokemon_char():
    result = await search_pokemon_data("char", limit=5)

    names = [item.name for item in result.matches]

    assert result.count > 0
    assert "charmander" in names
    assert "charmeleon" in names
    assert "charizard" in names