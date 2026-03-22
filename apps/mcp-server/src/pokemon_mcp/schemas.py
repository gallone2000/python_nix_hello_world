from pydantic import BaseModel


class PokemonStats(BaseModel):
    hp: int | None = None
    attack: int | None = None
    defense: int | None = None
    special_attack: int | None = None
    special_defense: int | None = None
    speed: int | None = None


class PokemonResponse(BaseModel):
    name: str
    id: int
    types: list[str]
    abilities: list[str]
    stats: PokemonStats
    image_url: str | None = None


class PokemonSpeciesResponse(BaseModel):
    name: str
    id: int
    genus: str | None = None
    habitat: str | None = None
    color: str | None = None
    shape: str | None = None
    is_legendary: bool = False
    is_mythical: bool = False
    flavor_text: str | None = None


class PokemonSearchItem(BaseModel):
    name: str
    id: int
    image_url: str | None = None


class PokemonSearchResponse(BaseModel):
    query: str
    count: int
    matches: list[PokemonSearchItem]


class PokemonByTypeResponse(BaseModel):
    type: str
    count: int
    pokemon: list[str]


class TypeMatchupResponse(BaseModel):
    type: str
    double_damage_to: list[str]
    double_damage_from: list[str]
    half_damage_to: list[str]
    half_damage_from: list[str]
    no_damage_to: list[str]
    no_damage_from: list[str]


class EvolutionChainResponse(BaseModel):
    pokemon: str
    species: str
    chain: list[str]


class PokemonComparisonItem(BaseModel):
    name: str
    id: int
    types: list[str]
    abilities: list[str]
    stats: PokemonStats
    image_url: str | None = None


class StatDifferences(BaseModel):
    hp: int | None = None
    attack: int | None = None
    defense: int | None = None
    special_attack: int | None = None
    special_defense: int | None = None
    speed: int | None = None


class ComparePokemonResponse(BaseModel):
    pokemon_1: PokemonComparisonItem
    pokemon_2: PokemonComparisonItem
    stat_differences: StatDifferences
    higher_stats_pokemon_1: list[str]
    higher_stats_pokemon_2: list[str]