"""Command line interface."""

from argparse import (
    Action,
    ArgumentParser,
)
from datetime import datetime

from pandas import DataFrame
from flask import Flask, request, jsonify, render_template
from penn_chime.constants import CHANGE_DATE
from penn_chime.parameters import Parameters, Disposition
from penn_chime.models import SimSirModel as Model
from penn_chime.settings import get_defaults

app = Flask(__name__)
class FromFile(Action):
    """From File."""

    def __call__(self, parser, namespace, values, option_string=None):
        with values as f:
            parser.parse_args(f.read().split(), namespace)


def cast_date(string):
    return datetime.strptime(string, '%Y-%m-%d').date()


def validator(arg, cast, min_value, max_value, required=True):
    """Validator."""

    def validate(string):
        """Validate."""
        if string == '' and cast != str:
            if required:
                raise AssertionError('%s is required.')
            return None
        value = cast(string)
        if min_value is not None:
            assert value >= min_value
        if max_value is not None:
            assert value <= max_value
        return value

    return validate


def parse_args():
    """Parse args."""
    parser = ArgumentParser(description=f"penn_chime: {CHANGE_DATE}")
    parser.add_argument("--file", type=open, action=FromFile)

    for arg, cast, min_value, max_value, help, required in (
        (
            "--current-hospitalized",
            int,
            0,
            None,
            "Currently hospitalized COVID-19 patients (>= 0)",
            True,
        ),
        (
            "--date-first-hospitalized",
            cast_date,
            None,
            None,
            "Current date",
            False,
        ),
        (
            "--doubling-time",
            float,
            0.0,
            None,
            "Doubling time before social distancing (days)",
            True,
        ),
        ("--hospitalized-days", int, 0, None, "Average hospital length of stay (in days)", True),
        (
            "--hospitalized-rate",
            float,
            0.00001,
            1.0,
            "Hospitalized Rate: 0.00001 - 1.0",
            True,
        ),
        ("--icu-days", int, 0, None, "Average days in ICU", True),
        ("--icu-rate", float, 0.0, 1.0, "ICU rate: 0.0 - 1.0", True),
        (
            "--market_share",
            float,
            0.00001,
            1.0,
            "Hospital market share (0.00001 - 1.0)",
            True,
        ),
        ("--infectious-days", float, 0.0, None, "Infectious days", True),
        ("--n-days", int, 0, None, "Number of days to project >= 0", True),
        (
            "--relative-contact-rate",
            float,
            0.0,
            1.0,
            "Social distancing reduction rate: 0.0 - 1.0",
            True,
        ),
        ("--population", int, 1, None, "Regional population >= 1", True),
        ("--ventilated-days", int, 0, None, "Average days on ventilator", True),
        ("--ventilated-rate", float, 0.0, 1.0, "Ventilated Rate: 0.0 - 1.0", True),
    ):
        parser.add_argument(
            arg,
            type=validator(arg, cast, min_value, max_value, required),
            help=help,
        )
    return parser.parse_args()


# def main():
#     """Main."""
#     # a = parse_args()
#     #
#     # p = Parameters(
#     #     current_hospitalized=a.current_hospitalized,
#     #     date_first_hospitalized=a.date_first_hospitalized,
#     #     doubling_time=a.doubling_time,
#     #     infectious_days=a.infectious_days,
#     #     market_share=a.market_share,
#     #     n_days=a.n_days,
#     #     relative_contact_rate=a.relative_contact_rate,
#     #     population=a.population,
#     #
#     #     hospitalized=Disposition(a.hospitalized_rate, a.hospitalized_days),
#     #     icu=Disposition(a.icu_rate, a.icu_days),
#     #     ventilated=Disposition(a.ventilated_rate, a.ventilated_days),
#     # )
#     p = get_defaults()
#     print(p.doubling_time, p.date_first_hospitalized)
#     m = Model(p)
#
#     for df, name in (
#         (m.sim_sir_w_date_df, "sim_sir_w_date"),
#         (m.admits_df, "projected_admits"),
#         (m.census_df, "projected_census"),
#     ):
#         df.to_csv(f"{p.current_date}_{name}.csv")

# if __name__ == "__main__":
#     main()

@app.route('/results',methods=['POST'])
def results():

    data = request.get_json(force=True)
    if 'date_first_hospitalized' in data.keys():
        data = Parameters(
            population=int(data["population"]),
            current_hospitalized=int(data["current_hospitalized"]),
            date_first_hospitalized=datetime.strptime(data["date_first_hospitalized"], "%Y/%m/%d").date(),
            # doubling_time=float(data["doubling_time"]),
            hospitalized=Disposition(float(data["hospitalized_rate"]), int(data["hospitalized_days"])),
            icu=Disposition(float(data["icu_rate"]), int(data["icu_days"])),
            infectious_days=int(data["infectious_days"]),
            market_share=float(data["market_share"]),
            n_days=int(data["n_days"]),
            mitigation_date=datetime.strptime(data["mitigation_date"], "%Y/%m/%d").date(),
            relative_contact_rate=float(data["relative_contact_rate"]),
            ventilated=Disposition(float(data["ventilated_rate"]), int(data["ventilated_days"])),
        )
    else:
        data = Parameters(
            population=int(data["population"]),
            current_hospitalized=int(data["current_hospitalized"]),
            # date_first_hospitalized=datetime.strptime(data["date_first_hospitalized"], "%Y/%m/%d").date(),
            doubling_time=float(data["doubling_time"]),
            hospitalized=Disposition(float(data["hospitalized_rate"]), int(data["hospitalized_days"])),
            icu=Disposition(float(data["icu_rate"]), int(data["icu_days"])),
            infectious_days=int(data["infectious_days"]),
            market_share=float(data["market_share"]),
            n_days=int(data["n_days"]),
            mitigation_date=datetime.strptime(data["mitigation_date"], "%Y/%m/%d").date(),
            relative_contact_rate=float(data["relative_contact_rate"]),
            ventilated=Disposition(float(data["ventilated_rate"]), int(data["ventilated_days"])),
        )
    print(data.date_first_hospitalized)
    m = Model(data)
    for df, name in (
            (m.sim_sir_w_date_df, "sim_sir_w_date"),
            (m.admits_df, "projected_admits"),
            (m.census_df, "projected_census"),
        ):
            df.to_csv(f"{data.current_date}_{name}.csv")
    return jsonify(df.iloc[-1].to_json())

if __name__ == "__main__":
    app.run(debug=True)
