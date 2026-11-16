from __future__ import annotations

from typing import Any, Mapping

from jinja2 import BaseLoader, Environment, StrictUndefined, TemplateError, meta


_MARKDOWN_TEMPLATE_ENV = Environment(
    loader=BaseLoader(),
    autoescape=False,
    trim_blocks=True,
    lstrip_blocks=True,
    undefined=StrictUndefined,
)


def _render_markdown(
    markdown_text: str,
    template_context: Mapping[str, Any] | None = None,
) -> str:
    """
    Render a Markdown string as a Jinja2 template.

    Example:
        markdown = '''
        {%- if ok %}
        - 允许输出 `1`
        {% endif -%}
        '''
        rendered = _render_markdown(
            markdown,
            {"ok": True},
        )
    """
    if not isinstance(markdown_text, str):
        raise TypeError("markdown_text must be a string")

    try:
        context = dict(template_context or {})
        parsed = _MARKDOWN_TEMPLATE_ENV.parse(markdown_text)
        for variable_name in meta.find_undeclared_variables(parsed):
            if variable_name.startswith("enable_"):
                context.setdefault(variable_name, False)

        template = _MARKDOWN_TEMPLATE_ENV.from_string(markdown_text)
        return template.render(**context)
    except TemplateError as exc:
        raise ValueError(f"failed to render markdown template: {exc}") from exc


__all__ = ["_render_markdown"]

if __name__ == "__main__":
    markdown = """
测试
{% if "face_shape" in get_skills_tool_config %}
- 当前允许请求 `face_shape`
{% endif -%}
{%- if bpa["beautyParams"]["contrast"]["status"]=="allow" %}
  - 图片偏暗、层次不明显时，可优先考虑 `contrast`
{% endif %}
{%- if bpa["beautyParams"]["contrast"]["status"]=="1" %}
  - 测试3
{% endif %}
  - 测试2
- 测试4
- {% if "face_shape" in get_skills_tool_config %}`face_shape`{% endif -%}{%- if bpa["beautyParams"]["contrast"]["status"]=="allow" %}`contrast`{% endif %}


    """

    template_context = {
        "get_skills_tool_config": ["basic_beauty", "filter", "face_shape"],
        'bpa': {
          'beautyParams': {
            'status': 'partial',
            'whitten': {
              'status': 'allow',
              'info': {
                'status': 'allow',
                'nature': {
                  'status': 'allow'
                },
                'original': {
                  'status': 'allow'
                },
                'pink': {
                  'status': 'allow'
                },
                'black': {
                  'status': 'allow'
                },
                'cold': {
                  'status': 'allow'
                }
              }
            },
            'redden': {
              'status': 'deny'
            },
            'faceSmooth': {
              'status': 'deny'
            },
            'contrast': {
              'status': 'allow'
            },
            'saturation': {
              'status': 'deny'
            },
            'sharpen': {
              'status': 'deny'
            },
            'clear': {
              'status': 'deny'
            },
            'denoising': {
              'status': 'deny'
            },
            'colorTone': {
              'status': 'deny'
            },
            'colorTemperature': {
              'status': 'deny'
            },
            'shrinkFace': {
              'status': 'deny'
            },
            'enlargeEye': {
              'status': 'deny'
            },
            'shrinkJaw': {
              'status': 'deny'
            },
            'narrowFace': {
              'status': 'deny'
            },
            'roundEye': {
              'status': 'deny'
            },
            'thinnerHead': {
              'status': 'deny'
            },
            'thinFace': {
              'status': 'deny'
            },
            'chinLength': {
              'status': 'deny'
            },
            'hairlineHeight': {
              'status': 'deny'
            },
            'appleMusle': {
              'status': 'deny'
            },
            'narrowNose': {
              'status': 'deny'
            },
            'noseLength': {
              'status': 'deny'
            },
            'profileRhinoplasty': {
              'status': 'deny'
            },
            'mouthSize': {
              'status': 'deny'
            },
            'philtrumLength': {
              'status': 'deny'
            },
            'eyeDistance': {
              'status': 'deny'
            },
            'eyeAngle': {
              'status': 'deny'
            },
            'openCanthus': {
              'status': 'deny'
            },
            'brightEye': {
              'status': 'deny'
            },
            'removeDarkCircles': {
              'status': 'deny'
            },
            'removeNasolabialFolds': {
              'status': 'deny'
            },
            'whiteTeeth': {
              'status': 'deny'
            },
            'shrinkCheekbone': {
              'status': 'deny'
            },
            'openExternalCanthus': {
              'status': 'deny'
            },
            'shrinkJawbone': {
              'status': 'deny'
            },
            'shrinkRoundFace': {
              'status': 'deny'
            },
            'shrinkLongFace': {
              'status': 'deny'
            },
            'shrinkGoddessFace': {
              'status': 'deny'
            },
            'shrinkNaturalFace': {
              'status': 'deny'
            },
            'shrinkWholeHead': {
              'status': 'deny'
            },
            'eyeHeight': {
              'status': 'deny'
            },
            'mouthCorner': {
              'status': 'deny'
            },
            'hairline': {
              'status': 'deny'
            },
            'fullerLips': {
              'status': 'deny'
            },
            'mouthWidth': {
              'status': 'deny'
            },
            'browHeight': {
              'status': 'deny'
            },
            'browThickness': {
              'status': 'deny'
            },
            'browDistance': {
              'status': 'deny'
            },
            'faceVShape': {
              'status': 'deny'
            },
            'faceFullVShape': {
              'status': 'deny'
            },
            'noseTip': {
              'status': 'deny'
            },
            'enlargePupil': {
              'status': 'deny'
            },
            'filter': {
              'status': 'deny',
              'info': {
                'status': 'deny',
                'zg_mingfu2': {
                  'status': 'deny'
                },
                'jp_fj2': {
                  'status': 'deny'
                },
                'zg_yelin': {
                  'status': 'deny'
                },
                'jp_guoqijuan2': {
                  'status': 'deny'
                },
                'zg_mingfu': {
                  'status': 'deny'
                },
                'jp_fanhua1': {
                  'status': 'deny'
                },
                'jp_cpm35': {
                  'status': 'deny'
                },
                'ek1': {
                  'status': 'deny'
                },
                'tianju': {
                  'status': 'deny'
                },
                'hongyun2': {
                  'status': 'deny'
                },
                'fenbai2': {
                  'status': 'deny'
                },
                'laika11': {
                  'status': 'deny'
                }
              }
            },
            'lipstick': {
              'status': 'deny',
              'info': {
                'status': 'deny',
                '11nature': {
                  'status': 'deny'
                },
                '12nature': {
                  'status': 'deny'
                },
                '6nature': {
                  'status': 'deny'
                },
                '1fog': {
                  'status': 'deny'
                },
                '3fog': {
                  'status': 'deny'
                },
                '5fog': {
                  'status': 'deny'
                },
                '7fog': {
                  'status': 'deny'
                },
                '9fog': {
                  'status': 'deny'
                },
                '10nature': {
                  'status': 'deny'
                },
                '9water': {
                  'status': 'deny'
                },
                '5water': {
                  'status': 'deny'
                }
              }
            },
            'cheek': {
              'status': 'allow',
              'info': {
                'status': 'allow',
                'blusha': {
                  'status': 'allow'
                },
                'blushd': {
                  'status': 'allow'
                }
              }
            },
            'nose': {
              'status': 'deny',
              'info': {
                'status': 'deny',
                'faceb': {
                  'status': 'deny'
                },
                'faced': {
                  'status': 'deny'
                }
              }
            },
            'eyeBrow': {
              'status': 'deny',
              'info': {
                'status': 'deny',
                'browb': {
                  'status': 'deny'
                },
                'browd': {
                  'status': 'deny'
                },
                'browe': {
                  'status': 'deny'
                }
              }
            },
            'eyeShadow': {
              'status': 'deny',
              'info': {
                'status': 'deny',
                'eyeshadg': {
                  'status': 'deny'
                },
                'eyeshadh': {
                  'status': 'deny'
                }
              }
            },
            'eyeLiner': {
              'status': 'deny',
              'info': {
                'status': 'deny',
                'eyelineri': {
                  'status': 'deny'
                },
                'eyelinera': {
                  'status': 'deny'
                }
              }
            },
            'eyeLash': {
              'status': 'partial',
              'info': {
                'status': 'partial',
                'eyelashE': {
                  'status': 'allow'
                },
                'eyelashK': {
                  'status': 'allow'
                },
                'eyelashL': {
                  'status': 'deny'
                },
                'eyelashM': {
                  'status': 'deny'
                }
              }
            },
            'doubleEyelid': {
              'status': 'deny',
              'info': {
                'status': 'deny',
                'doubleEyelidA': {
                  'status': 'deny'
                },
                'doubleEyelidB': {
                  'status': 'deny'
                }
              }
            },
            'aegyoSal': {
              'status': 'deny',
              'info': {
                'status': 'deny',
                'aegyoSalA': {
                  'status': 'deny'
                }
              }
            },
            'eyeBall': {
              'status': 'deny',
              'info': {
                'status': 'deny',
                'eyeballd': {
                  'status': 'deny'
                }
              }
            },
            'ganSkin': {
              'status': 'deny'
            },
            'texureCreamy': {
              'status': 'deny'
            },
            'texureGlassy': {
              'status': 'deny'
            },
            'texureHd': {
              'status': 'deny'
            },
            'texureMatte': {
              'status': 'deny'
            },
            'bodyWhole': {
              'status': 'deny'
            },
            'bodyHead': {
              'status': 'deny'
            },
            'bodyShoulder': {
              'status': 'deny'
            },
            'bodyWaist': {
              'status': 'deny'
            },
            'bodyHip': {
              'status': 'deny'
            },
            'bodyLeg': {
              'status': 'deny'
            },
            'bodyHeight': {
              'status': 'deny'
            },
            'bodyNeck': {
              'status': 'deny'
            },
            'bodyChest': {
              'status': 'deny'
            },
            'bodySquareShoulder': {
              'status': 'deny'
            },
            'bodyArm': {
              'status': 'deny'
            },
            'bodyNeckSlim': {
              'status': 'deny'
            },
            'bodyNeckLength': {
              'status': 'deny'
            }
          },
          'style': {
            'status': 'deny',
            'info': {
              'status': 'deny',
              'qingchun': {
                'status': 'deny'
              },
              'hanshi': {
                'status': 'deny'
              },
              'western': {
                'status': 'deny'
              }
            }
          }
        }

    }

    rendered = _render_markdown(
        markdown,
        template_context
    )
    print(rendered)
