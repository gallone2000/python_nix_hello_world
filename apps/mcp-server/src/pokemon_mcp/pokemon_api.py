import asyncio
import httpx

from pokemon_mcp.schemas import (
    ComparePokemonResponse,
    EvolutionChainResponse,
    PokemonByTypeResponse,
    PokemonComparisonItem,
    PokemonResponse,
    PokemonSearchItem,
    PokemonSearchResponse,
    PokemonSpeciesResponse,
    PokemonStats,
    StatDifferences,
    TypeMatchupResponse,
)
from pokemon_mcp.settings import settings

_http_client: httpx.AsyncClient | None = None


class PokemonAPIError(Exception):
    """User-friendly error for Pokemon MCP tool responses."""


_http_client: httpx.AsyncClient | None = None
_http_client_loop: asyncio.AbstractEventLoop | None = None


def _get_client() -> httpx.AsyncClient:
    global _http_client, _http_client_loop

    current_loop = asyncio.get_running_loop()

    if (
        _http_client is None
        or _http_client.is_closed
        or _http_client_loop is not current_loop
    ):
        _http_client = httpx.AsyncClient(timeout=settings.http_timeout_seconds)
        _http_client_loop = current_loop

    return _http_client


async def close_http_client() -> None:
    global _http_client, _http_client_loop

    client = _http_client
    _http_client = None
    _http_client_loop = None

    if client is None or client.is_closed:
        return

    try:
        await client.aclose()
    except RuntimeError:
        pass


def _normalize_value(value: str, field_name: str) -> str:
    normalized = value.strip().lower()
    if not normalized:
        raise PokemonAPIError(f"{field_name} cannot be empty")
    return normalized


def _normalize_limit(
    limit: int | None,
    *,
    default: int = 10,
    min_value: int = 1,
    max_value: int = 50,
) -> int:
    if limit is None:
        return default
    return max(min_value, min(limit, max_value))


def _validate_distinct_pokemon(pokemon_1: str, pokemon_2: str) -> tuple[str, str]:
    value_1 = _normalize_value(pokemon_1, "pokemon_1")
    value_2 = _normalize_value(pokemon_2, "pokemon_2")

    if value_1 == value_2:
        raise PokemonAPIError("pokemon_1 and pokemon_2 must be different")

    return value_1, value_2


async def _request_json(
    url: str,
    *,
    not_found_message: str | None = None,
) -> dict:
    try:
        response = await _get_client().get(url)

        if response.status_code == 404 and not_found_message is not None:
            raise PokemonAPIError(not_found_message)

        response.raise_for_status()
        return response.json()

    except PokemonAPIError:
        raise
    except httpx.TimeoutException as exc:
        raise PokemonAPIError("PokeAPI request timed out") from exc
    except httpx.ConnectError as exc:
        raise PokemonAPIError("Could not reach PokeAPI") from exc
    except httpx.HTTPStatusError as exc:
        status_code = exc.response.status_code if exc.response is not None else "unknown"
        raise PokemonAPIError(f"PokeAPI returned HTTP {status_code}") from exc
    except httpx.HTTPError as exc:
        raise PokemonAPIError("Unexpected PokeAPI error") from exc


async def fetch_pokemon_raw(name_or_id: str) -> dict:
    value = _normalize_value(name_or_id, "name_or_id")
    url = f"{settings.pokeapi_base_url}/pokemon/{value}"
    return await _request_json(url, not_found_message=f"Pokemon not found: {value}")


async def fetch_type_raw(type_name: str) -> dict:
    value = _normalize_value(type_name, "type_name")
    url = f"{settings.pokeapi_base_url}/type/{value}"
    return await _request_json(url, not_found_message=f"Pokemon type not found: {value}")


async def fetch_pokemon_species_raw(name_or_id: str) -> dict:
    value = _normalize_value(name_or_id, "name_or_id")
    url = f"{settings.pokeapi_base_url}/pokemon-species/{value}"
    return await _request_json(url, not_found_message=f"Pokemon species not found: {value}")


async def fetch_pokemon_index_raw() -> dict:
    url = f"{settings.pokeapi_base_url}/pokemon?limit=2000&offset=0"
    return await _request_json(url)


async def fetch_json_by_url(url: str) -> dict:
    return await _request_json(url)


def _build_stats(payload: dict) -> PokemonStats:
    stats_map = {
        item["stat"]["name"]: item["base_stat"]
        for item in payload.get("stats", [])
    }

    return PokemonStats(
        hp=stats_map.get("hp"),
        attack=stats_map.get("attack"),
        defense=stats_map.get("defense"),
        special_attack=stats_map.get("special-attack"),
        special_defense=stats_map.get("special-defense"),
        speed=stats_map.get("speed"),
    )


def _extract_image_url(payload: dict) -> str | None:
    sprites = payload.get("sprites", {}) or {}
    other = sprites.get("other", {}) or {}
    official_artwork = other.get("official-artwork", {}) or {}

    return official_artwork.get("front_default") or sprites.get("front_default")


def simplify_pokemon_payload(payload: dict) -> PokemonResponse:
    abilities = [
        item["ability"]["name"]
        for item in payload.get("abilities", [])
    ]

    types = [
        item["type"]["name"]
        for item in sorted(payload.get("types", []), key=lambda x: x["slot"])
    ]

    stats = _build_stats(payload)

    return PokemonResponse(
        name=payload["name"],
        id=payload["id"],
        types=types,
        abilities=abilities,
        stats=stats,
        image_url=_extract_image_url(payload),
    )


def _search_rank(query: str, name: str) -> tuple[int, int, str] | None:
    if name == query:
        return (0, len(name), name)

    if name.startswith(query):
        return (1, len(name), name)

    if query in name:
        return (2, len(name), name)

    return None


async def _build_search_item(name: str) -> PokemonSearchItem:
    payload = await fetch_pokemon_raw(name)
    return PokemonSearchItem(
        name=payload["name"],
        id=payload["id"],
        image_url=_extract_image_url(payload),
    )


async def simplify_pokemon_search_payload(
    query: str,
    payload: dict,
    limit: int,
) -> PokemonSearchResponse:
    results = payload.get("results", []) or []

    ranked_matches: list[tuple[tuple[int, int, str], str]] = []

    for item in results:
        name = item.get("name", "").lower()
        rank = _search_rank(query, name)
        if rank is not None:
            ranked_matches.append((rank, name))

    ranked_matches.sort(key=lambda item: item[0])

    selected_names = [name for _, name in ranked_matches[:limit]]
    matches = await asyncio.gather(*(_build_search_item(name) for name in selected_names))

    return PokemonSearchResponse(
        query=query,
        count=len(matches),
        matches=matches,
    )


def simplify_type_payload(payload: dict, limit: int = 10) -> PokemonByTypeResponse:
    pokemon_names = [
        item["pokemon"]["name"]
        for item in payload.get("pokemon", [])[:limit]
    ]

    return PokemonByTypeResponse(
        type=payload["name"],
        count=len(pokemon_names),
        pokemon=pokemon_names,
    )


def simplify_type_matchup_payload(payload: dict) -> TypeMatchupResponse:
    damage_relations = payload.get("damage_relations", {}) or {}

    def names(key: str) -> list[str]:
        return [item["name"] for item in damage_relations.get(key, [])]

    return TypeMatchupResponse(
        type=payload["name"],
        double_damage_to=names("double_damage_to"),
        double_damage_from=names("double_damage_from"),
        half_damage_to=names("half_damage_to"),
        half_damage_from=names("half_damage_from"),
        no_damage_to=names("no_damage_to"),
        no_damage_from=names("no_damage_from"),
    )


def _flatten_evolution_chain(chain_node: dict) -> list[str]:
    names: list[str] = []

    def walk(node: dict) -> None:
        species = node.get("species", {}) or {}
        name = species.get("name")
        if name:
            names.append(name)

        for child in node.get("evolves_to", []) or []:
            walk(child)

    walk(chain_node)
    return names


def simplify_evolution_chain_payload(
    pokemon_name: str,
    species_payload: dict,
    evolution_chain_payload: dict,
) -> EvolutionChainResponse:
    chain_root = evolution_chain_payload.get("chain", {}) or {}
    chain = _flatten_evolution_chain(chain_root)

    return EvolutionChainResponse(
        pokemon=pokemon_name,
        species=species_payload.get("name", pokemon_name),
        chain=chain,
    )


def _get_english_genus(payload: dict) -> str | None:
    for item in payload.get("genera", []):
        language = item.get("language", {}) or {}
        if language.get("name") == "en":
            return item.get("genus")
    return None


def _get_english_flavor_text(payload: dict) -> str | None:
    for item in payload.get("flavor_text_entries", []):
        language = item.get("language", {}) or {}
        if language.get("name") != "en":
            continue

        text = item.get("flavor_text")
        if not text:
            continue

        return text.replace("\n", " ").replace("\f", " ").strip()

    return None


def simplify_pokemon_species_payload(payload: dict) -> PokemonSpeciesResponse:
    habitat = payload.get("habitat")
    color = payload.get("color")
    shape = payload.get("shape")

    return PokemonSpeciesResponse(
        name=payload["name"],
        id=payload["id"],
        genus=_get_english_genus(payload),
        habitat=habitat.get("name") if habitat else None,
        color=color.get("name") if color else None,
        shape=shape.get("name") if shape else None,
        is_legendary=bool(payload.get("is_legendary", False)),
        is_mythical=bool(payload.get("is_mythical", False)),
        flavor_text=_get_english_flavor_text(payload),
    )


def _comparison_item_from_payload(payload: dict) -> PokemonComparisonItem:
    abilities = [
        item["ability"]["name"]
        for item in payload.get("abilities", [])
    ]

    types = [
        item["type"]["name"]
        for item in sorted(payload.get("types", []), key=lambda x: x["slot"])
    ]

    return PokemonComparisonItem(
        name=payload["name"],
        id=payload["id"],
        types=types,
        abilities=abilities,
        stats=_build_stats(payload),
        image_url=_extract_image_url(payload),
    )


def _stat_diff(a: int | None, b: int | None) -> int | None:
    if a is None or b is None:
        return None
    return a - b


def simplify_compare_pokemon_payload(
    payload_1: dict,
    payload_2: dict,
) -> ComparePokemonResponse:
    pokemon_1 = _comparison_item_from_payload(payload_1)
    pokemon_2 = _comparison_item_from_payload(payload_2)

    stat_differences = StatDifferences(
        hp=_stat_diff(pokemon_1.stats.hp, pokemon_2.stats.hp),
        attack=_stat_diff(pokemon_1.stats.attack, pokemon_2.stats.attack),
        defense=_stat_diff(pokemon_1.stats.defense, pokemon_2.stats.defense),
        special_attack=_stat_diff(
            pokemon_1.stats.special_attack,
            pokemon_2.stats.special_attack,
        ),
        special_defense=_stat_diff(
            pokemon_1.stats.special_defense,
            pokemon_2.stats.special_defense,
        ),
        speed=_stat_diff(pokemon_1.stats.speed, pokemon_2.stats.speed),
    )

    higher_stats_pokemon_1: list[str] = []
    higher_stats_pokemon_2: list[str] = []

    comparisons = {
        "hp": stat_differences.hp,
        "attack": stat_differences.attack,
        "defense": stat_differences.defense,
        "special_attack": stat_differences.special_attack,
        "special_defense": stat_differences.special_defense,
        "speed": stat_differences.speed,
    }

    for stat_name, diff in comparisons.items():
        if diff is None or diff == 0:
            continue
        if diff > 0:
            higher_stats_pokemon_1.append(stat_name)
        else:
            higher_stats_pokemon_2.append(stat_name)

    return ComparePokemonResponse(
        pokemon_1=pokemon_1,
        pokemon_2=pokemon_2,
        stat_differences=stat_differences,
        higher_stats_pokemon_1=higher_stats_pokemon_1,
        higher_stats_pokemon_2=higher_stats_pokemon_2,
    )


async def get_pokemon_data(name_or_id: str) -> PokemonResponse:
    payload = await fetch_pokemon_raw(name_or_id)
    return simplify_pokemon_payload(payload)


async def get_pokemon_species_data(name_or_id: str) -> PokemonSpeciesResponse:
    payload = await fetch_pokemon_species_raw(name_or_id)
    return simplify_pokemon_species_payload(payload)


async def search_pokemon_data(query: str, limit: int | None = 10) -> PokemonSearchResponse:
    normalized_query = _normalize_value(query, "query")
    safe_limit = _normalize_limit(limit)
    payload = await fetch_pokemon_index_raw()
    return await simplify_pokemon_search_payload(normalized_query, payload, safe_limit)


async def get_pokemon_by_type(type_name: str, limit: int | None = 10) -> PokemonByTypeResponse:
    safe_limit = _normalize_limit(limit)
    payload = await fetch_type_raw(type_name)
    return simplify_type_payload(payload, limit=safe_limit)


async def get_type_matchup_data(type_name: str) -> TypeMatchupResponse:
    payload = await fetch_type_raw(type_name)
    return simplify_type_matchup_payload(payload)


async def get_evolution_chain_data(name_or_id: str) -> EvolutionChainResponse:
    normalized_name_or_id = _normalize_value(name_or_id, "name_or_id")
    species_payload = await fetch_pokemon_species_raw(normalized_name_or_id)

    evolution_chain_info = species_payload.get("evolution_chain", {}) or {}
    evolution_chain_url = evolution_chain_info.get("url")
    if not evolution_chain_url:
        raise PokemonAPIError(f"No evolution chain found for '{normalized_name_or_id}'")

    evolution_chain_payload = await fetch_json_by_url(evolution_chain_url)

    return simplify_evolution_chain_payload(
        pokemon_name=normalized_name_or_id,
        species_payload=species_payload,
        evolution_chain_payload=evolution_chain_payload,
    )


async def compare_pokemon_data(pokemon_1: str, pokemon_2: str) -> ComparePokemonResponse:
    normalized_pokemon_1, normalized_pokemon_2 = _validate_distinct_pokemon(
        pokemon_1,
        pokemon_2,
    )

    payload_1 = await fetch_pokemon_raw(normalized_pokemon_1)
    payload_2 = await fetch_pokemon_raw(normalized_pokemon_2)

    return simplify_compare_pokemon_payload(payload_1, payload_2)