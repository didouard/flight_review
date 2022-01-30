





    data = ulog.data_list

    test = [elem for elem in data if elem.name == "estimator_status"][0]
    data = test.data
    vibe = data.get("vibe[2]")

    warning = 0
    critical = 0
    for v in vibe:
        if v >= 0.02:
            warning += 1
        elif v >= 0.04:
            critical += 1

    return