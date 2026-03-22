import asyncio

import pytest

from pokemon_mcp.pokemon_api import (
    PokemonAPIError,
    close_http_client,
    compare_pokemon_data,
    get_evolution_chain_data,
    get_pokemon_by_type,
    get_pokemon_data,
    get_pokemon_species_data,
    get_type_matchup_data,
    search_pokemon_data,
)


class MockResponse:
    def __init__(self, json_data: dict, status_code: int = 200):
        self._json_data = json_data
        self.status_code = status_code

    def json(self) -> dict:
        return self._json_data

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            import httpx

            request = httpx.Request("GET", "https://pokeapi.co/api/v2/mock")
            response = httpx.Response(self.status_code, request=request)
            raise httpx.HTTPStatusError(
                f"HTTP {self.status_code}",
                request=request,
                response=response,
            )


@pytest.fixture(autouse=True)
def cleanup_http_client():
    yield
    asyncio.run(close_http_client())


@pytest.fixture
def mock_pokeapi(monkeypatch):
    pikachu_payload = {
        "name": "pikachu",
        "id": 25,
        "abilities": [
            {"ability": {"name": "static"}},
            {"ability": {"name": "lightning-rod"}},
        ],
        "types": [
            {"slot": 1, "type": {"name": "electric"}},
        ],
        "stats": [
            {"stat": {"name": "hp"}, "base_stat": 35},
            {"stat": {"name": "attack"}, "base_stat": 55},
            {"stat": {"name": "defense"}, "base_stat": 40},
            {"stat": {"name": "special-attack"}, "base_stat": 50},
            {"stat": {"name": "special-defense"}, "base_stat": 50},
            {"stat": {"name": "speed"}, "base_stat": 90},
        ],
        "sprites": {
            "front_default": "https://img.test/pikachu-sprite.png",
            "other": {
                "official-artwork": {
                    "front_default": "https://img.test/pikachu.png",
                }
            },
        },
    }

    raichu_payload = {
        "name": "raichu",
        "id": 26,
        "abilities": [
            {"ability": {"name": "static"}},
        ],
        "types": [
            {"slot": 1, "type": {"name": "electric"}},
        ],
        "stats": [
            {"stat": {"name": "hp"}, "base_stat": 60},
            {"stat": {"name": "attack"}, "base_stat": 90},
            {"stat": {"name": "defense"}, "base_stat": 55},
            {"stat": {"name": "special-attack"}, "base_stat": 90},
            {"stat": {"name": "special-defense"}, "base_stat": 80},
            {"stat": {"name": "speed"}, "base_stat": 110},
        ],
        "sprites": {
            "front_default": "https://img.test/raichu-sprite.png",
            "other": {
                "official-artwork": {
                    "front_default": "https://img.test/raichu.png",
                }
            },
        },
    }

    charmander_payload = {
        "name": "charmander",
        "id": 4,
        "abilities": [{"ability": {"name": "blaze"}}],
        "types": [{"slot": 1, "type": {"name": "fire"}}],
        "stats": [
            {"stat": {"name": "hp"}, "base_stat": 39},
            {"stat": {"name": "attack"}, "base_stat": 52},
            {"stat": {"name": "defense"}, "base_stat": 43},
            {"stat": {"name": "special-attack"}, "base_stat": 60},
            {"stat": {"name": "special-defense"}, "base_stat": 50},
            {"stat": {"name": "speed"}, "base_stat": 65},
        ],
        "sprites": {
            "front_default": "https://img.test/charmander-sprite.png",
            "other": {
                "official-artwork": {
                    "front_default": "https://img.test/charmander.png",
                }
            },
        },
    }

    charmeleon_payload = {
        "name": "charmeleon",
        "id": 5,
        "abilities": [{"ability": {"name": "blaze"}}],
        "types": [{"slot": 1, "type": {"name": "fire"}}],
        "stats": [
            {"stat": {"name": "hp"}, "base_stat": 58},
            {"stat": {"name": "attack"}, "base_stat": 64},
            {"stat": {"name": "defense"}, "base_stat": 58},
            {"stat": {"name": "special-attack"}, "base_stat": 80},
            {"stat": {"name": "special-defense"}, "base_stat": 65},
            {"stat": {"name": "speed"}, "base_stat": 80},
        ],
        "sprites": {
            "front_default": "https://img.test/charmeleon-sprite.png",
            "other": {
                "official-artwork": {
                    "front_default": "https://img.test/charmeleon.png",
                }
            },
        },
    }

    charizard_payload = {
        "name": "charizard",
        "id": 6,
        "abilities": [{"ability": {"name": "blaze"}}],
        "types": [
            {"slot": 1, "type": {"name": "fire"}},
            {"slot": 2, "type": {"name": "flying"}},
        ],
        "stats": [
            {"stat": {"name": "hp"}, "base_stat": 78},
            {"stat": {"name": "attack"}, "base_stat": 84},
            {"stat": {"name": "defense"}, "base_stat": 78},
            {"stat": {"name": "special-attack"}, "base_stat": 109},
            {"stat": {"name": "special-defense"}, "base_stat": 85},
            {"stat": {"name": "speed"}, "base_stat": 100},
        ],
        "sprites": {
            "front_default": "https://img.test/charizard-sprite.png",
            "other": {
                "official-artwork": {
                    "front_default": "https://img.test/charizard.png",
                }
            },
        },
    }

    bulbasaur_payload = {
        "name": "bulbasaur",
        "id": 1,
        "abilities": [{"ability": {"name": "overgrow"}}],
        "types": [
            {"slot": 1, "type": {"name": "grass"}},
            {"slot": 2, "type": {"name": "poison"}},
        ],
        "stats": [
            {"stat": {"name": "hp"}, "base_stat": 45},
            {"stat": {"name": "attack"}, "base_stat": 49},
            {"stat": {"name": "defense"}, "base_stat": 49},
            {"stat": {"name": "special-attack"}, "base_stat": 65},
            {"stat": {"name": "special-defense"}, "base_stat": 65},
            {"stat": {"name": "speed"}, "base_stat": 45},
        ],
        "sprites": {
            "front_default": "https://img.test/bulbasaur-sprite.png",
            "other": {
                "official-artwork": {
                    "front_default": "https://img.test/bulbasaur.png",
                }
            },
        },
    }

    ivysaur_payload = {
        "name": "ivysaur",
        "id": 2,
        "abilities": [{"ability": {"name": "overgrow"}}],
        "types": [
            {"slot": 1, "type": {"name": "grass"}},
            {"slot": 2, "type": {"name": "poison"}},
        ],
        "stats": [
            {"stat": {"name": "hp"}, "base_stat": 60},
            {"stat": {"name": "attack"}, "base_stat": 62},
            {"stat": {"name": "defense"}, "base_stat": 63},
            {"stat": {"name": "special-attack"}, "base_stat": 80},
            {"stat": {"name": "special-defense"}, "base_stat": 80},
            {"stat": {"name": "speed"}, "base_stat": 60},
        ],
        "sprites": {
            "front_default": "https://img.test/ivysaur-sprite.png",
            "other": {
                "official-artwork": {
                    "front_default": "https://img.test/ivysaur.png",
                }
            },
        },
    }

    venusaur_payload = {
        "name": "venusaur",
        "id": 3,
        "abilities": [{"ability": {"name": "overgrow"}}],
        "types": [
            {"slot": 1, "type": {"name": "grass"}},
            {"slot": 2, "type": {"name": "poison"}},
        ],
        "stats": [
            {"stat": {"name": "hp"}, "base_stat": 80},
            {"stat": {"name": "attack"}, "base_stat": 82},
            {"stat": {"name": "defense"}, "base_stat": 83},
            {"stat": {"name": "special-attack"}, "base_stat": 100},
            {"stat": {"name": "special-defense"}, "base_stat": 100},
            {"stat": {"name": "speed"}, "base_stat": 80},
        ],
        "sprites": {
            "front_default": "https://img.test/venusaur-sprite.png",
            "other": {
                "official-artwork": {
                    "front_default": "https://img.test/venusaur.png",
                }
            },
        },
    }

    bulbasaur_species_payload = {
        "name": "bulbasaur",
        "id": 1,
        "genera": [
            {"genus": "Seed Pokémon", "language": {"name": "en"}},
        ],
        "habitat": {"name": "grassland"},
        "color": {"name": "green"},
        "shape": {"name": "quadruped"},
        "is_legendary": False,
        "is_mythical": False,
        "flavor_text_entries": [
            {
                "flavor_text": "A strange seed was planted on its back at birth.",
                "language": {"name": "en"},
            }
        ],
        "evolution_chain": {
            "url": "https://pokeapi.co/api/v2/evolution-chain/1/",
        },
    }

    pikachu_species_payload = {
        "name": "pikachu",
        "id": 25,
        "genera": [
            {"genus": "Mouse Pokémon", "language": {"name": "en"}},
        ],
        "habitat": {"name": "forest"},
        "color": {"name": "yellow"},
        "shape": {"name": "quadruped"},
        "is_legendary": False,
        "is_mythical": False,
        "flavor_text_entries": [
            {
                "flavor_text": "When several of these Pokémon gather, their electricity could build and cause lightning storms.",
                "language": {"name": "en"},
            }
        ],
        "evolution_chain": {
            "url": "https://pokeapi.co/api/v2/evolution-chain/10/",
        },
    }

    mewtwo_species_payload = {
        "name": "mewtwo",
        "id": 150,
        "genera": [
            {"genus": "Genetic Pokémon", "language": {"name": "en"}},
        ],
        "habitat": None,
        "color": {"name": "purple"},
        "shape": {"name": "upright"},
        "is_legendary": True,
        "is_mythical": False,
        "flavor_text_entries": [
            {
                "flavor_text": "It was created by a scientist after years of horrific gene splicing and DNA engineering experiments.",
                "language": {"name": "en"},
            }
        ],
        "evolution_chain": {
            "url": "https://pokeapi.co/api/v2/evolution-chain/76/",
        },
    }

    electric_type_payload = {
        "name": "electric",
        "damage_relations": {
            "double_damage_to": [{"name": "water"}, {"name": "flying"}],
            "double_damage_from": [{"name": "ground"}],
            "half_damage_to": [{"name": "electric"}, {"name": "grass"}, {"name": "dragon"}],
            "half_damage_from": [{"name": "electric"}, {"name": "flying"}, {"name": "steel"}],
            "no_damage_to": [{"name": "ground"}],
            "no_damage_from": [],
        },
        "pokemon": [{"pokemon": {"name": f"electric-mon-{i}"}} for i in range(1, 101)],
    }

    fire_type_payload = {
        "name": "fire",
        "damage_relations": {
            "double_damage_to": [{"name": "grass"}, {"name": "ice"}, {"name": "bug"}, {"name": "steel"}],
            "double_damage_from": [{"name": "water"}, {"name": "ground"}, {"name": "rock"}],
            "half_damage_to": [{"name": "fire"}, {"name": "water"}, {"name": "rock"}, {"name": "dragon"}],
            "half_damage_from": [{"name": "fire"}, {"name": "grass"}, {"name": "ice"}, {"name": "bug"}, {"name": "steel"}, {"name": "fairy"}],
            "no_damage_to": [],
            "no_damage_from": [],
        },
        "pokemon": [
            {"pokemon": {"name": "charmander"}},
            {"pokemon": {"name": "charmeleon"}},
            {"pokemon": {"name": "charizard"}},
            {"pokemon": {"name": "vulpix"}},
            {"pokemon": {"name": "ninetales"}},
            {"pokemon": {"name": "growlithe"}},
            {"pokemon": {"name": "arcanine"}},
            {"pokemon": {"name": "ponyta"}},
            {"pokemon": {"name": "rapidash"}},
            {"pokemon": {"name": "magmar"}},
        ],
    }

    pokemon_index_payload = {
        "results": [
            {"name": "pikachu"},
            {"name": "raichu"},
            {"name": "pichu"},
            {"name": "charmander"},
            {"name": "charmeleon"},
            {"name": "charizard"},
            {"name": "bulbasaur"},
            {"name": "ivysaur"},
            {"name": "venusaur"},
            {"name": "squirtle"},
        ]
    }

    evolution_chain_1_payload = {
        "chain": {
            "species": {"name": "bulbasaur"},
            "evolves_to": [
                {
                    "species": {"name": "ivysaur"},
                    "evolves_to": [
                        {
                            "species": {"name": "venusaur"},
                            "evolves_to": [],
                        }
                    ],
                }
            ],
        }
    }

    payload_by_name = {
        "pikachu": pikachu_payload,
        "raichu": raichu_payload,
        "charmander": charmander_payload,
        "charmeleon": charmeleon_payload,
        "charizard": charizard_payload,
        "bulbasaur": bulbasaur_payload,
        "ivysaur": ivysaur_payload,
        "venusaur": venusaur_payload,
    }

    species_by_name = {
        "bulbasaur": bulbasaur_species_payload,
        "pikachu": pikachu_species_payload,
        "mewtwo": mewtwo_species_payload,
    }

    type_by_name = {
        "electric": electric_type_payload,
        "fire": fire_type_payload,
    }

    async def mock_get(self, url, *args, **kwargs):
        if "/pokemon?limit=2000&offset=0" in url:
            return MockResponse(pokemon_index_payload)

        if "/pokemon-species/" in url:
            name = url.rstrip("/").split("/")[-1]
            payload = species_by_name.get(name)
            if payload is None:
                return MockResponse({}, status_code=404)
            return MockResponse(payload)

        if "/type/" in url:
            type_name = url.rstrip("/").split("/")[-1]
            payload = type_by_name.get(type_name)
            if payload is None:
                return MockResponse({}, status_code=404)
            return MockResponse(payload)

        if "/evolution-chain/1/" in url:
            return MockResponse(evolution_chain_1_payload)

        if "/pokemon/" in url:
            name = url.rstrip("/").split("/")[-1]
            payload = payload_by_name.get(name)
            if payload is None:
                return MockResponse({}, status_code=404)
            return MockResponse(payload)

        return MockResponse({}, status_code=404)

    monkeypatch.setattr("httpx.AsyncClient.get", mock_get)


def test_get_pokemon_data_pikachu(mock_pokeapi):
    result = asyncio.run(get_pokemon_data("pikachu"))

    assert result.name == "pikachu"
    assert result.id == 25
    assert "electric" in result.types
    assert "static" in result.abilities
    assert result.stats.speed == 90
    assert result.image_url == "https://img.test/pikachu.png"


def test_get_pokemon_data_empty_name(mock_pokeapi):
    with pytest.raises(PokemonAPIError, match="name_or_id cannot be empty"):
        asyncio.run(get_pokemon_data(""))


def test_get_pokemon_data_not_found(mock_pokeapi):
    with pytest.raises(PokemonAPIError, match="Pokemon not found: not-a-real-pokemon"):
        asyncio.run(get_pokemon_data("not-a-real-pokemon"))


def test_get_pokemon_by_type_electric(mock_pokeapi):
    result = asyncio.run(get_pokemon_by_type("electric"))

    assert result.type == "electric"
    assert result.count == 10
    assert len(result.pokemon) == 10
    assert result.pokemon[0] == "electric-mon-1"


def test_get_pokemon_by_type_with_limit(mock_pokeapi):
    result = asyncio.run(get_pokemon_by_type("fire", limit=5))

    assert result.type == "fire"
    assert result.count == 5
    assert result.pokemon == [
        "charmander",
        "charmeleon",
        "charizard",
        "vulpix",
        "ninetales",
    ]


def test_get_type_matchup_fire(mock_pokeapi):
    result = asyncio.run(get_type_matchup_data("fire"))

    assert result.type == "fire"
    assert "grass" in result.double_damage_to
    assert "water" in result.double_damage_from
    assert "fire" in result.half_damage_from


def test_get_pokemon_species_pikachu(mock_pokeapi):
    result = asyncio.run(get_pokemon_species_data("pikachu"))

    assert result.name == "pikachu"
    assert result.id == 25
    assert result.genus == "Mouse Pokémon"
    assert result.habitat == "forest"
    assert result.color == "yellow"
    assert result.is_legendary is False
    assert result.flavor_text is not None


def test_get_pokemon_species_mewtwo_legendary(mock_pokeapi):
    result = asyncio.run(get_pokemon_species_data("mewtwo"))

    assert result.name == "mewtwo"
    assert result.is_legendary is True
    assert result.is_mythical is False


def test_get_evolution_chain_bulbasaur(mock_pokeapi):
    result = asyncio.run(get_evolution_chain_data("bulbasaur"))

    assert result.pokemon == "bulbasaur"
    assert result.species == "bulbasaur"
    assert result.chain == ["bulbasaur", "ivysaur", "venusaur"]


def test_compare_pokemon_pikachu_vs_raichu(mock_pokeapi):
    result = asyncio.run(compare_pokemon_data("pikachu", "raichu"))

    assert result.pokemon_1.name == "pikachu"
    assert result.pokemon_2.name == "raichu"
    assert result.stat_differences.speed == -20
    assert "speed" in result.higher_stats_pokemon_2
    assert result.pokemon_1.image_url == "https://img.test/pikachu.png"
    assert result.pokemon_2.image_url == "https://img.test/raichu.png"


def test_compare_pokemon_same_name_rejected(mock_pokeapi):
    with pytest.raises(PokemonAPIError, match="pokemon_1 and pokemon_2 must be different"):
        asyncio.run(compare_pokemon_data("pikachu", "pikachu"))


def test_search_pokemon_exact_match_ranked_first(mock_pokeapi):
    result = asyncio.run(search_pokemon_data("pikachu", limit=5))

    assert result.query == "pikachu"
    assert result.count >= 1
    assert result.matches[0].name == "pikachu"
    assert result.matches[0].id == 25
    assert result.matches[0].image_url == "https://img.test/pikachu.png"


def test_search_pokemon_prefix_match(mock_pokeapi):
    result = asyncio.run(search_pokemon_data("char", limit=10))

    names = [item.name for item in result.matches]

    assert names == ["charizard", "charmander", "charmeleon"]
    assert result.matches[0].id == 6


def test_search_pokemon_substring_match(mock_pokeapi):
    result = asyncio.run(search_pokemon_data("saur", limit=10))

    names = [item.name for item in result.matches]

    assert names == ["ivysaur", "venusaur", "bulbasaur"]


def test_search_pokemon_empty_query(mock_pokeapi):
    with pytest.raises(PokemonAPIError, match="query cannot be empty"):
        asyncio.run(search_pokemon_data(""))


def test_search_pokemon_returns_rich_items(mock_pokeapi):
    result = asyncio.run(search_pokemon_data("pika", limit=5))

    assert result.count == 1
    first = result.matches[0]
    assert first.name == "pikachu"
    assert first.id == 25
    assert first.image_url == "https://img.test/pikachu.png"