(Recipe Morning-shot (With-ingredient Ginger))
(Recipe Morning-shot (With-ingredient Orange))

(In-store Apple)
(In-store Banana)
(In-store Orange)

(Hate Apple)
(Hate Grape)
(Love Banana)
(Love Orange)
(Love Strawberry)

!(match &self (Love $fruit) (match &self (In-store $fruit)
    (join
        (Buy $fruit)
        (match &self (Recipe $recipe (With-ingredient $fruit))
            (match &self (Recipe $recipe (With-ingredient $ingredient))
                (Buy $ingredient)
            )
        )
    )
))
